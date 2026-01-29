"""
AI Workflows - Main Entry Point
================================

This module serves as the command-line interface for the AI Workflows framework.
It provides functionality for generating workflows from natural language prompts
and executing previously generated workflows.

Key Capabilities:
    - Workflow generation using configurable strategies (monolithic, incremental,
      bottom-up)
    - Workflow execution with tool invocation
    - Multi-run experiments with random prompt selection
    - Feature pipeline configuration (clarification, refinement, validation)
    - Flexible agent configuration per role

Supported LLM Providers:
    - Cerebras: gpt-oss, llama-3.3
    - Google: gemini-2.5-flash, gemini-2.5-flash-lite

Usage Examples:
    Generate a workflow:
        python main.py --generate --prompt weather_activity_plan
    
    Generate and execute:
        python main.py --generate --execute --strategy bottomup
    
    Execute existing workflow:
        python main.py --execute --workflow-path data/workflows/workflow_1.json
    
    Multi-run experiment:
        python main.py --generate --runs 10 --random-it

See Also:
    evaluate.py for workflow evaluation and metric computation.
"""

import argparse
import random

from datetime import datetime
from agents.google import GeminiAgent, GeminiModel
from agents.cerebras import CerebrasAgent, CerebrasModel
from features import ChatClarificationFeature, RefinementFeature, ValidationRefinementFeature
from models.workflows import LinearWorkflow, StructuredWorkflow
from orchestrators import ConfigurableOrchestrator
from strategies import MonolithicStrategy, IncrementalStrategy, BottomUpStrategy
from tools.tool import ToolType
from tools.registry import ToolRegistry
from utils.prompt import PromptUtils
from utils.metric import MetricUtils
from utils.workflow import WorkflowUtils


# ---------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------

# Agent/model mapping: CLI spec → (AgentClass, ModelEnum)
AGENT_MODELS = {
    # Cerebras models
    "cerebras:gpt-oss": (CerebrasAgent, CerebrasModel.GPT_OSS),
    "cerebras:llama-3.3": (CerebrasAgent, CerebrasModel.LLAMA_3_3),
    # Gemini models
    "gemini:2.5-flash": (GeminiAgent, GeminiModel.GEMINI_2_5_FLASH),
    "gemini:2.5-flash-lite": (GeminiAgent, GeminiModel.GEMINI_2_5_FLASH_LITE),
}

AGENT_CHOICES = list(AGENT_MODELS.keys())


def _agents_factory(args):
    """
    Build agents dictionary from CLI arguments.
    
    Creates agent instances for specified roles. Unspecified roles
    will use the default agent configured in AgentSchema.
    
    Args:
        args: Parsed argparse namespace with agent specifications.
        
    Returns:
        Dict mapping role names to AgentBase instances.
        
    Raises:
        ValueError: If unknown agent specification provided.
    """
    agents = {}
    
    # Map CLI arg names to agent schema keys
    agent_args = {
        "generator": args.generator,
        "reviewer": args.reviewer,
        "planner": args.planner,
        "chatter": args.chatter,
        "refiner": args.refiner,
        "executor": args.executor,
    }
    
    for name, spec in agent_args.items():
        if spec:
            if spec not in AGENT_MODELS:
                raise ValueError(f"Unknown agent '{spec}' for '{name}'. Valid: {', '.join(AGENT_CHOICES)}")
            agent_cls, model = AGENT_MODELS[spec]
            agents[name] = agent_cls(model)
    
    return agents


def _strategy_factory(name: str):
    """
    Create strategy instance from name.
    
    Args:
        name: Strategy name (monolithic, incremental, bottomup).
        
    Returns:
        Configured strategy instance.
        
    Raises:
        ValueError: If unknown strategy name.
    """
    mapping = {
        "monolithic": MonolithicStrategy,
        "incremental": IncrementalStrategy,
        "bottomup": BottomUpStrategy
    }
    cls = mapping.get(name.lower())
    if cls is None:
        raise ValueError(f"Unknown strategy '{name}'. Valid: {', '.join(mapping.keys())}")
    return cls()


def _workflow_model_factory(name: str):
    """
    Get workflow model class from name.
    
    Args:
        name: Workflow type (linear, structured).
        
    Returns:
        Workflow model class (not instance).
        
    Raises:
        ValueError: If unknown workflow type.
    """
    mapping = {
        "linear": LinearWorkflow,
        "structured": StructuredWorkflow,
    }
    cls = mapping.get(name.lower())
    if cls is None:
        raise ValueError(f"Unknown workflow model '{name}'. Valid: {', '.join(mapping.keys())}")
    return cls


def _tools_factory(args):
    """
    Build list of available tools based on CLI filters.
    
    Supports filtering by tool type (atomic/macro) and specific
    tool selection by name.
    
    Args:
        args: Parsed argparse namespace with tool options.
        
    Returns:
        List of Tool instances available for workflow execution.
    """
    if args.no_tools:
        return []
    
    if args.atomic_tools_only:
        all_tools = ToolRegistry.get_by_type(ToolType.ATOMIC)
    elif args.macro_tools_only:
        all_tools = ToolRegistry.get_by_type(ToolType.MACRO)
    else:
        all_tools = ToolRegistry.get_all_tools()

    if not args.select_tools:
        return all_tools
    
    # Filter to selected tools only
    selected_tools = []
    for tool_name in args.select_tools:
        selected_tools.append(tool for tool in all_tools if tool.name == tool_name)

    return selected_tools


def _features_factory(args):
    """
    Build list of enabled features from CLI flags.
    
    Args:
        args: Parsed argparse namespace with feature flags.
        
    Returns:
        List of FeatureBase instances to include in pipeline.
    """
    selected_features = []
    if args.chat:
        selected_features.append(ChatClarificationFeature())
    if args.refinement:
        selected_features.append(RefinementFeature())
    if args.validation_refinement:
        selected_features.append(ValidationRefinementFeature())
    return selected_features


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    """
    Main entry point for CLI workflow operations.
    
    Parses command-line arguments and orchestrates workflow generation
    and/or execution based on user options. Supports multi-run experiments
    with metric tracking across runs.
    """
    # Argument parsing
    argparser = argparse.ArgumentParser(description="AI Workflow Orchestrator")

    # =========================================================
    # Core Settings
    # =========================================================
    argparser.add_argument("--runs", type=int, default=1, help="Number of sequential runs to execute (default: 1)")
    argparser.add_argument("--it", type=int, default=1, help="Pick a specific iteration for prompt (generate) or workflow (execute)")
    argparser.add_argument("--random-it", action="store_true", help="Pick a random iteration for prompt (generate) or workflow (execute)")

    # =========================================================
    # Generation Settings
    # =========================================================
    argparser.add_argument("--generate", action="store_true", help="Generate a workflow from the given prompt")
    argparser.add_argument("--prompt", type=str, default="weather_activity_plan", help="User prompt name to use")

    # Strategy & workflow model
    argparser.add_argument("--strategy", type=str, choices=["monolithic", "incremental", "bottomup"], default="monolithic",
                            help="Which orchestration strategy to use (default: monolithic)")
    argparser.add_argument("--workflow-model", type=str, choices=["linear", "structured"], default="structured",
                            help="Which workflow class to use for generation / loading (default: structured)")

    # Features
    argparser.add_argument("--chat", action="store_true", help="Enable ChatClarificationFeature")
    argparser.add_argument("--refinement", action="store_true", help="Enable RefinementFeature")
    argparser.add_argument("--validation-refinement", action="store_true", help="Enable ValidationRefinementFeature")

    # Tools
    argparser.add_argument("--select-tools", nargs="+", help="Subset of tools to enable (by name) (default: all tools)")
    argparser.add_argument("--atomic-tools-only", action="store_true", help="Enable only atomic tools")
    argparser.add_argument("--macro-tools-only", action="store_true", help="Enable only macro tools")
    argparser.add_argument("--no-tools", action="store_true", help="Disable all tools")

    # =========================================================
    # Agent Settings
    # =========================================================
    agent_help = f"Agent spec in format 'provider:model'. Choices: {', '.join(AGENT_CHOICES)}"
    argparser.add_argument("--generator", type=str, metavar="AGENT", help=f"Generator agent. {agent_help}")
    argparser.add_argument("--reviewer", type=str, metavar="AGENT", help=f"Reviewer agent. {agent_help}")
    argparser.add_argument("--planner", type=str, metavar="AGENT", help=f"Planner agent. {agent_help}")
    argparser.add_argument("--chatter", type=str, metavar="AGENT", help=f"Chatter agent. {agent_help}")
    argparser.add_argument("--refiner", type=str, metavar="AGENT", help=f"Refiner agent. {agent_help}")
    argparser.add_argument("--executor", type=str, metavar="AGENT", help=f"Executor agent. {agent_help}")

    # =========================================================
    # Execution Settings
    # =========================================================
    argparser.add_argument("--execute", action="store_true", help="Execute the generated or loaded workflow")
    argparser.add_argument("--workflow-path", type=str, help="Path to a saved workflow JSON to load when not generating")

    # =========================================================
    # Reporting Settings
    # =========================================================
    argparser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = argparser.parse_args()

    # Prepare orchestrator components
    strategy_instance = _strategy_factory(args.strategy)
    workflow_model_cls = _workflow_model_factory(args.workflow_model)
    available_tools = _tools_factory(args)
    selected_features = _features_factory(args)
    configured_agents = _agents_factory(args)

    random_idx = -1
    iterations_idx = []
    formatted_metrics = []
    for run in range(args.runs):
        print(f"\n{'='*40}\nRun {run + 1} of {args.runs}\n{'='*40}\n")

        # Reset metrics and random seed between runs
        MetricUtils.reset()
        random.seed(int(datetime.now().strftime("%Y%m%d%H%M%S")) + run)

        # Configure the orchestrator with chosen strategy and tools
        orchestrator = ConfigurableOrchestrator(
            strategy=strategy_instance,
            available_tools=available_tools,
            agents=configured_agents,
            features=selected_features
        )

        # Determine the user intention
        if args.generate:
                
            prompts = PromptUtils.get_user_prompts(args.prompt)
            
            if args.random_it:
                random_idx = random.choice([i for i in range(1, len(prompts) + 1) if i not in iterations_idx])
                iterations_idx.append(random_idx)
            else:
                random_idx = args.it  # Use the specified iteration (default: 1)

            # Pick the random prompt for this iteration
            user_prompt = prompts.get(str(random_idx))

            print(f"User Prompt (iteration {random_idx}): {user_prompt}\n")

            # Generate the workflow
            context = orchestrator.generate(
                user_prompt=user_prompt, 
                response_model=workflow_model_cls,
                debug=args.debug
            )

            # If also executing, run it 
            if args.execute:
                orchestrator.run(context.workflow_path, debug=args.debug)  
            
        elif args.execute:
            
            workflow_files = WorkflowUtils.list_workflows()
            
            if args.workflow_path:
                workflow_path = args.workflow_path
            elif args.random_it:
                random_idx = random.choice([i for i in range(0, len(workflow_files)) if i not in iterations_idx])
                iterations_idx.append(random_idx)
                workflow_path = workflow_files[random_idx]
            else:
                workflow_path = workflow_files[0] # Pick the first one by default
            
            print(f"Workflow: {workflow_path}\n")
            
            # Execute the workflow
            orchestrator.run(workflow_path, debug=args.debug)
        else:
            raise ValueError("At least one of --generate or --execute must be specified.")

        # Display metrics
        formatted_metrics.append(MetricUtils.display())
    
    MetricUtils.display_formatted_metrics(formatted_metrics)

if __name__ == "__main__":
    main()

