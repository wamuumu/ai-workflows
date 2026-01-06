import time

from models.bottom_up import ToolAnalysisResponse, ControlFlowResponse
from strategies.base import StrategyBase
from tools.registry import ToolRegistry
from utils.prompt import PromptUtils

class BottomUpStrategy(StrategyBase):
    """Bottom-up construction strategy: identify tools → order them → add control flow."""

    def __init__(self):
        super().__init__()

    def generate(self, context, max_retries, debug):
        
        agents = context.agents
        user_prompt = context.prompt
        available_tools = context.available_tools
        response_model = context.response_model

        if debug:
            print("Generating workflow with BottomUpStrategy...")
            print("User Prompt:", user_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")

        if not agents.generator:
            raise ValueError("Generator agent not found.")
        
        if not agents.planner:
            raise ValueError("Planner agent not found (used for analysis phases).")

        # Phase 1: Identify required tools
        retry = 0
        while retry < max_retries:
            try:
                tool_analysis = self._identify_tools(agents.planner, user_prompt, available_tools, debug)
                break
            except Exception as e:
                retry += 1
                retry_time = 2 ** retry
                print(f"Identification retry {retry}/{max_retries} after error: {e}. Retrying in {retry_time} seconds...")
                time.sleep(retry_time)
        
        if retry == max_retries:
            raise RuntimeError("Max retries exceeded during tool identification.")
        
        # Phase 2: Identify control flow needs
        retry = 0
        while retry < max_retries:
            try:
                control_flow = self._identify_control_flow(agents.planner, user_prompt, tool_analysis, debug)
                break
            except Exception as e:
                retry += 1
                retry_time = 2 ** retry
                print(f"Control flow retry {retry}/{max_retries} after error: {e}. Retrying in {retry_time} seconds...")
                time.sleep(retry_time)

        if retry == max_retries:
            raise RuntimeError("Max retries exceeded during flow control identification.")
        
        # Phase 3: Assemble complete workflow
        retry = 0
        while retry < max_retries:
            try:
                return self._assemble_workflow(
                    agents.generator,
                    user_prompt,
                    tool_analysis,
                    control_flow,
                    response_model
                )
            except Exception as e:
                retry += 1
                retry_time = 2 ** retry
                print(f"Assemble retry {retry}/{max_retries} after error: {e}. Retrying in {retry_time} seconds...")
                time.sleep(retry_time)
        
        if retry == max_retries:
            raise RuntimeError("Max retries exceeded during workflow assemble.")

    def _identify_tools(self, agent, user_prompt: str, available_tools: list, debug: bool) -> ToolAnalysisResponse:
        """Phase 1: Identify which tools are needed."""
        
        system_prompt = PromptUtils.get_system_prompt("tool_identification")
        system_prompt_with_tools = PromptUtils.inject(
            system_prompt,
            ToolRegistry.to_prompt_format(tools=available_tools)
        )

        response = agent.generate_structured_content(
            system_prompt_with_tools,
            user_prompt,
            ToolAnalysisResponse
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

    def _identify_control_flow(self, agent, user_prompt: str, tool_analysis: ToolAnalysisResponse, debug: bool) -> ControlFlowResponse:
        """Phase 2: Identify where control flow (branching, conditionals) is needed."""

        tools = ""
        for tool in tool_analysis.required_tools:
            tools += ToolRegistry.get(tool.tool_name).to_prompt_format() + "\n"
        
        system_prompt = PromptUtils.get_system_prompt("flow_identification")
        context = PromptUtils.inject(user_prompt, ordered_tools=tools)

        response = agent.generate_structured_content(
            system_prompt,
            context,
            ControlFlowResponse
        )
        
        if debug:
            print("\n=== PHASE 2: Control Flow Identification ===")
            print(f"Reasoning: {response.reasoning}")
            print(f"Control decisions ({len(response.control_decisions)}):")
            for decision in response.control_decisions:
                print(f"  At {decision.decision_point}: {decision.decision_type} - {decision.reason}")
                print(f"    Branches: {', '.join(decision.branches) if decision.branches else 'none'}")
            print(f"LLM calls needed: {', '.join(response.llm_calls_needed) if response.llm_calls_needed else 'none'}")
            input("Press Enter to continue...")
        
        return response

    def _assemble_workflow(self, agent, user_prompt: str, tool_analysis: ToolAnalysisResponse, control_flow: ControlFlowResponse, response_model):
        """Phase 3: Assemble complete workflow from analysis."""
        
        system_prompt = PromptUtils.get_system_prompt("workflow_generation")
        
        # Build detailed assembly instructions
        assembly_context = f"""

        ## Original User Request
        {user_prompt}

        ## Tools to use (Pre-Analyzed)
        """
        for tool in tool_analysis.required_tools:
            assembly_context += ToolRegistry.get(tool.tool_name).to_prompt_format() + "\n"

        assembly_context += "\n## Control Flow Requirements (Pre-Analyzed)\n"
        for decision in control_flow.control_decisions:
            assembly_context += f"- {decision.decision_point}: {decision.decision_type} - {decision.reason}\n"
            if decision.branches:
                assembly_context += f"  Branches: {', '.join(decision.branches)}\n"

        if control_flow.llm_calls_needed:
            assembly_context += f"\n## LLM Reasoning Required At: {', '.join(control_flow.llm_calls_needed)}\n"

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
        
        workflow = agent.generate_structured_content(
            system_prompt,
            assembly_context,
            response_model
        )
        
        return workflow