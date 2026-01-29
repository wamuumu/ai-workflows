"""
Orchestrators Base Module
=========================

This module defines the core orchestration infrastructure for the AI Workflows
framework. The ConfigurableOrchestrator class serves as the central coordination
point for workflow generation and execution.

Key Components:
    - AgentSchema: Pydantic model defining role-specific agents for different
      phases of workflow processing (generation, review, planning, etc.)
    - Context: Data transfer object carrying state through the orchestration
      pipeline, including inputs, outputs, and intermediate results
    - ConfigurableOrchestrator: Main orchestration engine that coordinates
      agents, strategies, and features to produce and execute workflows

Architecture Pattern:
    The orchestrator implements a pipeline pattern where:
    1. Pre-features modify context before generation (e.g., clarification)
    2. Strategy generates the workflow based on context
    3. Post-features refine the generated workflow (e.g., validation)
    4. Execution engine runs the workflow with tool invocations

Runtime Directory:
    Tool execution occurs in an isolated runtime directory to prevent
    filesystem conflicts and ensure reproducible execution environments.
"""

import os
import json
import logging
import shutil

from pydantic import BaseModel, Field, field_serializer
from typing import Optional, Type, List
from contextlib import contextmanager
from agents.base import AgentBase
from agents.google import GeminiAgent, GeminiModel
from agents.cerebras import CerebrasAgent, CerebrasModel
from features.base import FeatureBase
from models.responses.execution_response import ExecutionResponse
from strategies.base import StrategyBase
from tools.registry import Tool, ToolRegistry
from utils.prompt import PromptUtils
from utils.workflow import WorkflowUtils
from utils.metric import MetricUtils
from utils.logger import LoggerUtils

# Compute project root for locating runtime directories
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RUNTIME_DIR = os.path.join(ROOT, "data", "runtime", "tools")

# Initialize clean runtime directory on module load
shutil.rmtree(RUNTIME_DIR, ignore_errors=True)
os.makedirs(RUNTIME_DIR)


@contextmanager
def working_directory(path):
    """
    Context manager for temporarily changing the working directory.
    
    Enables tool execution in an isolated directory while preserving
    the original working directory after execution completes.
    
    Args:
        path: Target directory path to change to.
        
    Yields:
        None; working directory is changed for the duration of the context.
        
    Note:
        Original directory is restored even if an exception occurs.
    """
    old_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_cwd)


class AgentSchema(BaseModel):
    """
    Schema defining role-specific agents for workflow processing.
    
    Each agent role corresponds to a specific phase in the workflow
    lifecycle. Different models can be assigned to different roles
    to optimize for cost, latency, or capability requirements.
    
    Attributes:
        generator: Agent for generating workflow steps.
        reviewer: Agent for reviewing and validating workflows.
        planner: Agent for high-level workflow planning.
        chatter: Agent for user interaction and clarification.
        refiner: Agent for refining and improving workflows.
        executor: Agent for executing workflow steps.
        
    Configuration:
        - arbitrary_types_allowed: Permits AgentBase subclass instances
        - All agents default to CerebrasAgent with GPT_OSS model
    """
    generator: Optional[AgentBase] = Field(default_factory=lambda: CerebrasAgent(CerebrasModel.GPT_OSS))
    reviewer: Optional[AgentBase] = Field(default_factory=lambda: CerebrasAgent(CerebrasModel.GPT_OSS))
    planner: Optional[AgentBase] = Field(default_factory=lambda: CerebrasAgent(CerebrasModel.GPT_OSS))
    chatter: Optional[AgentBase] = Field(default_factory=lambda: CerebrasAgent(CerebrasModel.GPT_OSS))
    refiner: Optional[AgentBase] = Field(default_factory=lambda: CerebrasAgent(CerebrasModel.GPT_OSS))
    executor: Optional[AgentBase] = Field(default_factory=lambda: CerebrasAgent(CerebrasModel.GPT_OSS))

    model_config = { "arbitrary_types_allowed": True }

    @field_serializer("*")
    def serialize(self, agent):
        """
        Serialize agent instances to dictionary representation.
        
        Args:
            agent: AgentBase instance to serialize.
            
        Returns:
            Dict with agent type and model name, or None if agent is None.
        """
        if agent is None:
            return None
        return {
            "type": agent.__class__.__name__,
            "model": getattr(agent, "model_name", None)
        }


class Context(BaseModel):
    """
    Data transfer object for orchestration pipeline state.
    
    Carries both input configuration and output results through
    the orchestration pipeline. Modified by features and strategies
    as workflow generation progresses.
    
    Attributes:
        agents: Agent configuration for different workflow phases.
        response_model: Pydantic model class for workflow output format.
        prompt: User's original workflow request.
        available_tools: Tools available for workflow step execution.
        workflow: Generated workflow instance (populated after generation).
        workflow_path: File path where workflow JSON is saved.
        workflow_visualization_path: File path for HTML visualization.
        
    Serialization:
        Custom serializers handle complex types (models, tools, workflows)
        for JSON export and logging purposes.
    """
    # Input context for orchestrator operations
    agents: AgentSchema
    response_model: Type[BaseModel]
    prompt: str
    available_tools: List[Tool] 

    # Output context 
    workflow: Optional[BaseModel] = None
    workflow_path: Optional[str] = None
    workflow_visualization_path: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True}

    @field_serializer("response_model")
    def serialize_response_model(self, model):
        """Serialize response model to its class name."""
        return model.__name__

    @field_serializer("available_tools")
    def serialize_tools(self, tools):
        """Serialize tool list to list of tool names."""
        return [tool.name for tool in tools]
    
    @field_serializer("workflow")
    def serialize_workflow(self, workflow):
        """Serialize workflow to JSON-compatible dictionary."""
        if workflow is None:
            return None
        return json.loads(workflow.model_dump_json(indent=2))

class ConfigurableOrchestrator:
    """
    Main orchestration engine for workflow generation and execution.
    
    Coordinates the complete workflow lifecycle by:
        1. Applying pre-generation features (e.g., user clarification)
        2. Invoking strategy-based workflow generation
        3. Applying post-generation features (e.g., validation, refinement)
        4. Executing workflows with tool invocation
    
    The orchestrator is highly configurable, supporting different:
        - Generation strategies (monolithic, incremental, bottom-up)
        - Agent configurations for each processing phase
        - Pre/post-processing features in the pipeline
        - Tool sets available for workflow steps
    
    Attributes:
        agents: AgentSchema containing role-specific agent instances.
        strategy: Strategy for workflow generation.
        available_tools: Tools available for workflow execution.
        pre_features: Features applied before generation.
        post_features: Features applied after generation.
        logger: Logger utility for operation tracking.
    """

    def __init__(self, strategy: StrategyBase, available_tools: List[Tool], agents: dict[str, AgentBase] = {}, features: list[FeatureBase] = []):
        """
        Initialize the orchestrator with configuration.
        
        Args:
            strategy: Generation strategy instance.
            available_tools: List of tools for workflow execution.
            agents: Dict mapping role names to agent instances.
            features: List of feature instances; automatically
                sorted into pre/post phases based on get_phase().
        """
        self.agents = AgentSchema(**agents)
        self.strategy = strategy
        self.available_tools = available_tools
        # Partition features by execution phase
        self.pre_features = [f for f in features if f.get_phase() == "pre"]
        self.post_features = [f for f in features if f.get_phase() == "post"]
        self.logger = LoggerUtils()
    
    def generate(self, user_prompt: str, response_model: BaseModel, max_retries: int = 5, show: bool = False, debug: bool = False) -> Context:
        """
        Generate a workflow from a user prompt.
        
        Executes the full generation pipeline:
            1. Initialize context with user prompt and configuration
            2. Apply pre-generation features (modify context)
            3. Invoke strategy to generate workflow
            4. Apply post-generation features (refine workflow)
            5. Save workflow and visualization to disk
        
        Args:
            user_prompt: Natural language description of desired workflow.
            response_model: Pydantic model class defining workflow format.
            max_retries: Maximum retry attempts for LLM calls.
            show: If True, display workflow visualization interactively.
            debug: If True, log detailed context at each step.
            
        Returns:
            Context containing generated workflow and metadata.
            
        Side Effects:
            - Saves workflow JSON to data/workflows/
            - Saves HTML visualization to data/visualizations/
            - Increments global run ID counter
        """

        self.logger.log(logging.INFO, f"Workflow generation started...")
        context = Context(agents=self.agents, response_model=response_model, prompt=user_prompt, available_tools=self.available_tools)

        if debug:
            self.logger.log(logging.INFO, f"Initial context: {context.model_dump_json(indent=2)}")
        
        for feature in self.pre_features:
            context: Context = feature.apply(context, max_retries, debug)
            self.logger.log(logging.INFO, f"Context after pre-feature '{feature.__class__.__name__}': {context.model_dump_json(indent=2)}")

        context.workflow = self.strategy.generate(context, max_retries, debug)

        self.logger.log(logging.INFO, f"Generated workflow: {context.workflow.model_dump_json(indent=2)}")

        for feature in self.post_features:
            context: Context = feature.apply(context, max_retries, debug)
            self.logger.log(logging.INFO, f"Context after post-feature '{feature.__class__.__name__}': {context.model_dump_json(indent=2)}")
        
        self.logger.log(logging.INFO, f"Workflow generation completed.")

        if show:
            try:
                WorkflowUtils.show(context.workflow)
            except Exception as e:
                self.logger.log(logging.ERROR, f"Error showing workflow: {e}")

        try:
            context.workflow_path = WorkflowUtils.save_workflow(context.workflow)
            context.workflow_visualization_path = WorkflowUtils.save_visualization(context.workflow, user_prompt)
            WorkflowUtils.increment_run_id()
            self.logger.log(logging.INFO, f"Workflow saved successfully.")
        except Exception as e:
            self.logger.log(logging.ERROR, f"Error saving workflow: {e}")
        
        return context

    def run(self, workflow_path: str, max_retries: int = 5, debug: bool = False) -> None:
        """
        Execute a previously generated workflow.
        
        Loads a workflow from disk and executes it step by step,
        invoking tools and LLM calls as specified by each step.
        Maintains execution state that flows between steps.
        
        Execution Flow:
            1. Load workflow from JSON file
            2. Initialize executor agent chat session
            3. Iteratively process steps until final step reached
            4. For each step, execute tool or LLM action
            5. Accumulate results in state dictionary
            6. Save execution results when complete
        
        Args:
            workflow_path: Path to workflow JSON file.
            max_retries: Maximum retry attempts for executor LLM calls.
            debug: If True, pause for user confirmation at each step.
            
        Raises:
            FileNotFoundError: If workflow file does not exist.
            ValueError: If executor agent not configured or invalid
                response schema received.
            RuntimeError: If tool execution fails.
            
        Side Effects:
            - Saves execution results to data/executions/
            - Records metrics via MetricUtils
            - Tools execute in isolated runtime directory
        """

        if not os.path.exists(workflow_path):
            raise FileNotFoundError(f"Workflow file not found: {workflow_path}")
        
        workflow = WorkflowUtils.load_workflow(workflow_path)

        # Extract workflow ID from filename for tracking
        wf_id = (os.path.splitext(workflow_path)[0]).split("_")[-1]
        WorkflowUtils.set_run_id(int(wf_id))

        print(f"Execution ID set to: {wf_id}\n")

        self.logger.log(logging.INFO, f"Workflow execution started...")

        if debug:
            self.logger.log(logging.INFO, "Running workflow...")
            input("Press Enter to continue or Ctrl+C to exit...")

        # State accumulates tool/LLM results keyed by step ID
        state = {}
        execution_prompt = PromptUtils.get_system_prompt("workflow_execution")

        if not self.agents.executor:
            raise ValueError("Executor agent not found.")

        # Initialize structured chat session for execution coordination
        chat_session = self.agents.executor.init_structured_chat(execution_prompt, ExecutionResponse)
        next_message = workflow.model_dump_json()

        # Main execution loop - process steps until final step
        while True:

            response = chat_session.send_message(next_message, category="execution", max_retries=max_retries)
            
            # Validate response against expected schema
            try:
                response_schema = ExecutionResponse.model_validate(response)
            except Exception as e:
                self.logger.log(logging.ERROR, f"Invalid execution response schema: {e}")
                raise ValueError(f"Invalid execution response schema: {e}")

            payload = response_schema.model_dump()
            self.logger.log(logging.INFO, f"Execution response received: {json.dumps(payload, indent=2)}")
            
            if debug:
                self.logger.log(logging.INFO, f"Response received: {json.dumps(payload, indent=2)}")
                input("Press Enter to continue or Ctrl+C to exit...")
            
            step = payload.get("step")

            step_id = str(step.get("id"))
            step_action = step.get("action")
            is_final = step.get("is_final")

            # Check for workflow completion
            if is_final:
                self.logger.log(logging.INFO, f"Final step '{step_id}' reached. Ending workflow execution.")
                break
            
            # Handle tool invocation action
            if step_action == "call_tool":
                tool_name = step.get("tool_name")
                # Convert parameter list to kwargs dict
                parameters = {p.get("key"): p.get("value") for p in step.get("parameters", [])}

                if debug:
                    self.logger.log(logging.INFO, f"Calling tool '{tool_name}' with: {parameters}")
                    input("Press Enter to continue or Ctrl+C to exit...")
                
                try:
                    # Execute tool in isolated runtime directory
                    with working_directory(RUNTIME_DIR):
                        tool = ToolRegistry.get(tool_name)
                        results = tool.run(**parameters)
                        self.logger.log(logging.INFO, f"Tool '{tool_name}' for step '{step_id}' executed with results: {json.dumps(results, indent=2)}")
                except Exception as e:
                    self.logger.log(logging.ERROR, f"Error executing tool '{tool_name}': {e}")
                    raise RuntimeError(f"Error executing tool '{tool_name}': {e}")
                
                # Store results in state for downstream steps
                state[step_id] = results
                next_message = json.dumps({
                    "state": state
                })
                
                if debug:
                    self.logger.log(logging.INFO, f"Tool '{tool_name}' returned: {results}")
                    input("Press Enter to continue or Ctrl+C to exit...")

            # Handle LLM-based action (no tool call)
            elif step_action == "call_llm":
                response = step.get("response")

                self.logger.log(logging.INFO, f"LLM action for step '{step_id}' with response: {response}")

                state[step_id] = response
                next_message = json.dumps({
                    "state": state
                })

                if debug:
                    self.logger.log(logging.INFO, f"LLM action for step '{step_id}' with response: {response}")
                    input("Press Enter to continue or Ctrl+C to exit...")
            else:
                # Unknown action type - fail fast
                self.logger.log(logging.ERROR, f"Unknown action '{step_action}' received during workflow execution.")
                raise ValueError(f"Unknown action '{step_action}' received during workflow execution.")
        
        # Finalize metrics and save execution results
        MetricUtils.finish()
        try:
            WorkflowUtils.save_execution(state)
            self.logger.log(logging.INFO, f"Workflow execution completed and saved.")
        except Exception as e:
            self.logger.log(logging.ERROR, f"Error saving workflow: {e}")