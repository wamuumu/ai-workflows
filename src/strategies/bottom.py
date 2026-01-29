"""
Bottom-Up Strategy Module
=========================

This module implements the BottomUpStrategy, a multi-phase workflow
generation approach that analyzes requirements before assembling
the final workflow.

Main Responsibilities:
    - Phase 1: Identify required tools from user prompt
    - Phase 2: Determine optimal execution order
    - Phase 3: Identify control flow requirements
    - Phase 4: Assemble complete workflow from analysis

Key Dependencies:
    - models.responses.bottom_up_analysis: For phase response models
    - strategies.base: For StrategyBase interface
    - tools.registry: For tool information and lookup
    - utils.prompt: For prompt template loading

Use Cases:
    - Complex workflows with many tool dependencies
    - Workflows requiring explicit branching logic
    - High-quality generation where analysis improves output

Architecture:
    Implements a pipeline of specialized analysis phases:
    1. ToolAnalysisResponse - identifies tools and their purposes
    2. ToolOrderingResponse - determines dependency-based ordering
    3. ControlFlowResponse - identifies branching and LLM call points
    4. Final assembly using accumulated analysis

Trade-offs:
    - Pros: Better structure, explicit dependency handling, clearer logic
    - Cons: More API calls, higher latency, more complex
"""

from models.responses.bottom_up_analysis import ToolAnalysisResponse, ToolOrderingResponse, ControlFlowResponse
from strategies.base import StrategyBase
from tools.registry import ToolRegistry
from utils.prompt import PromptUtils


class BottomUpStrategy(StrategyBase):
    """
    Multi-phase analysis-driven workflow generation strategy.
    
    Decomposes workflow generation into discrete analysis phases:
    tool identification, ordering, control flow analysis, and
    final assembly. This approach produces more structured and
    logically consistent workflows.
    
    Attributes:
        None specific to this strategy.
    
    Required Agents:
        - generator: Agent for final workflow assembly.
        - planner: Agent for analysis phases (tool ID, ordering, flow).
    
    Generation Pipeline:
        1. _identify_tools() - Determine which tools are needed
        2. _order_tools() - Establish execution dependencies
        3. _identify_control_flow() - Plan branching and conditions
        4. _assemble_workflow() - Build final workflow structure
    """

    def __init__(self):
        """Initialize the bottom-up strategy with no additional parameters."""
        super().__init__()

    def generate(self, context, max_retries, debug):
        """
        Generate workflow through multi-phase analysis and assembly.
        
        Executes four sequential phases to analyze the user's requirements
        and assemble a complete workflow based on the accumulated analysis.
        
        Args:
            context: Orchestrator context containing prompt, agents,
                tools, and response model specification.
            max_retries: Maximum retry attempts for LLM API calls.
            debug: Whether to enable debug output at each phase.
            
        Returns:
            Complete workflow model assembled from phase analyses.
            
        Raises:
            ValueError: If generator agent is not configured.
            ValueError: If planner agent is not configured.
        """
        agents = context.agents
        user_prompt = context.prompt
        available_tools = context.available_tools
        response_model = context.response_model

        if debug:
            print("Generating workflow with BottomUpStrategy...")
            print("User Prompt:", user_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")

        # Validate required agents
        if not agents.generator:
            raise ValueError("Generator agent not found.")
        
        if not agents.planner:
            raise ValueError("Planner agent not found (used for analysis phases).")

        # === Phase 1: Identify required tools ===
        tool_analysis = self._identify_tools(agents.planner, user_prompt, available_tools, max_retries, debug)
        
        # === Phase 2: Order tool calls ===
        tool_ordering = self._order_tools(agents.planner, user_prompt, tool_analysis, max_retries, debug)

        # === Phase 3: Identify control flow needs ===
        control_flow = self._identify_control_flow(agents.planner, user_prompt, tool_ordering, max_retries, debug)
        
        # === Phase 4: Assemble complete workflow ===
        return self._assemble_workflow(
            agents.generator,
            user_prompt,
            tool_analysis,
            control_flow,
            response_model,
            max_retries
        )

    def _identify_tools(self, agent, user_prompt: str, available_tools: list, max_retries: int, debug: bool) -> ToolAnalysisResponse:
        """
        Phase 1: Identify which tools are needed for the workflow.
        
        Analyzes the user prompt to determine which available tools
        should be used, their purposes, and input/output requirements.
        
        Args:
            agent: Planner agent for tool analysis.
            user_prompt: Original user request text.
            available_tools: List of available tool names.
            max_retries: Maximum retry attempts for LLM call.
            debug: Whether to print phase output.
            
        Returns:
            ToolAnalysisResponse containing required tools and rationale.
        """
        # Load and prepare tool identification prompt
        system_prompt = PromptUtils.get_system_prompt("tool_identification")
        system_prompt_with_tools = PromptUtils.inject(
            system_prompt,
            ToolRegistry.to_prompt_format(tools=available_tools)
        )

        response = agent.generate_structured_content(
            system_prompt_with_tools,
            user_prompt,
            response_model=ToolAnalysisResponse,
            max_retries=max_retries
        )
        
        if debug:
            print("\n=== PHASE 1: Tool Identification ===")
            print(f"Reasoning: {response.reasoning}")
            print(f"Required tools ({len(response.required_tools)}):")
            for tool in response.required_tools:
                print(f"  - {tool.tool_name}: {tool.purpose}")
                print(f"    Inputs: {', '.join(tool.inputs_needed)}")
                print(f"    Outputs: {', '.join(tool.outputs_produced)}")
            input("Press Enter to continue...")
        
        return response

    def _order_tools(self, agent, user_prompt: str, tool_analysis: ToolAnalysisResponse, max_retries: int, debug: bool) -> ToolOrderingResponse:
        """
        Phase 2: Determine execution order of tool calls.
        
        Analyzes dependencies between identified tools to establish
        the correct execution sequence based on input/output flows.
        
        Args:
            agent: Planner agent for ordering analysis.
            user_prompt: Original user request text.
            tool_analysis: Phase 1 output with identified tools.
            max_retries: Maximum retry attempts for LLM call.
            debug: Whether to print phase output.
            
        Returns:
            ToolOrderingResponse containing ordered tool call sequence.
        """
        # Format tool information for ordering analysis
        tool_list = "\n".join([
            f"- {t.tool_name}: {t.purpose}\n  Inputs: {', '.join(t.inputs_needed)}\n  Outputs: {', '.join(t.outputs_produced)}"
            for t in tool_analysis.required_tools
        ])
        
        system_prompt = PromptUtils.get_system_prompt("tool_ordering")
        context = PromptUtils.inject(user_prompt, required_tools=tool_list)

        response = agent.generate_structured_content(
            system_prompt,
            context,
            response_model=ToolOrderingResponse,
            max_retries=max_retries
        )
        
        if debug:
            print("\n=== PHASE 2: Tool Ordering ===")
            print(f"Reasoning: {response.reasoning}")
            print(f"Ordered calls ({len(response.ordered_calls)}):")
            input("Press Enter to continue...")
        
        return response

    def _identify_control_flow(self, agent, user_prompt: str, tool_ordering: ToolOrderingResponse, max_retries: int, debug: bool) -> ControlFlowResponse:
        """
        Phase 3: Identify where control flow is needed.
        
        Analyzes the ordered tool sequence to determine where
        branching, conditionals, and LLM reasoning steps are required.
        
        Args:
            agent: Planner agent for control flow analysis.
            user_prompt: Original user request text.
            tool_ordering: Phase 2 output with ordered tool calls.
            max_retries: Maximum retry attempts for LLM call.
            debug: Whether to print phase output.
            
        Returns:
            ControlFlowResponse containing control flow decisions.
        """
        # Format tool sequence for flow analysis
        tool_sequence = "\n".join([f"{i+1}. {tool}" for i, tool in enumerate(tool_ordering.ordered_calls)])

        system_prompt = PromptUtils.get_system_prompt("flow_identification")
        context = PromptUtils.inject(user_prompt, ordered_tools=tool_sequence)

        response = agent.generate_structured_content(
            system_prompt,
            context,
            response_model=ControlFlowResponse,
            max_retries=max_retries
        )
        
        if debug:
            print("\n=== PHASE 3: Control Flow Identification ===")
            print(f"Reasoning: {response.reasoning}")
            print(f"Control decisions ({len(response.control_decisions)}):")
            for decision in response.control_decisions:
                print(f"  At {decision.decision_point}: {decision.decision_type} - {decision.reason}")
                print(f"    Branches: {', '.join(decision.branches) if decision.branches else 'none'}")
            print(f"LLM calls needed: {', '.join(response.llm_calls_needed) if response.llm_calls_needed else 'none'}")
            input("Press Enter to continue...")
        
        return response

    def _assemble_workflow(self, agent, user_prompt: str, tool_analysis: ToolAnalysisResponse, control_flow: ControlFlowResponse, response_model, max_retries: int):
        """
        Phase 4: Assemble complete workflow from accumulated analysis.
        
        Combines all phase outputs into detailed assembly instructions
        and generates the final workflow structure.
        
        Args:
            agent: Generator agent for final workflow assembly.
            user_prompt: Original user request text.
            tool_analysis: Phase 1 output with identified tools.
            control_flow: Phase 3 output with control flow decisions.
            response_model: Target workflow model class.
            max_retries: Maximum retry attempts for LLM call.
            
        Returns:
            Complete workflow model matching response_model type.
        """
        system_prompt = PromptUtils.get_system_prompt("workflow_generation")
        
        # Build detailed assembly instructions from all phases
        assembly_context = f"""

        ## Original User Request
        {user_prompt}

        ## Tools to use (Pre-Analyzed)
        """
        # Include full tool specifications for identified tools
        for tool in tool_analysis.required_tools:
            assembly_context += ToolRegistry.get(tool.tool_name).to_prompt_format() + "\n"

        # Include control flow requirements
        assembly_context += "\n## Control Flow Requirements (Pre-Analyzed)\n"
        for decision in control_flow.control_decisions:
            assembly_context += f"- {decision.decision_point}: {decision.decision_type} - {decision.reason}\n"
            if decision.branches:
                assembly_context += f"  Branches: {', '.join(decision.branches)}\n"

        if control_flow.llm_calls_needed:
            assembly_context += f"\n## LLM Reasoning Required At: {', '.join(map(str, control_flow.llm_calls_needed))}\n"

        # Provide explicit assembly instructions
        assembly_context += """
        ## Assembly Instructions
        1. Use all identified tools
        2. Implement control flow decisions at specified points
        3. Add LLM steps where indicated for reasoning/decisions
        4. Create proper transitions for StructuredWorkflow
        5. Ensure all dependencies are satisfied through proper referencing
        6. Add a FinalStep at the end

        ## Critical
        - Follow the pre-analyzed structure closely
        - The tools and ordering are already determined
        - Your job is to implement them with proper parameters and transitions
        - Maintain the step IDs from the analysis"""
        
        return agent.generate_structured_content(
            system_prompt,
            assembly_context,
            response_model=response_model,
            max_retries=max_retries
        )