import argparse
import random
from pathlib import Path

from agents.google import GeminiAgent, GeminiModel
from agents.cerebras import CerebrasAgent, CerebrasModel
from features import ChatClarificationFeature, RefinementFeature
from models import LinearWorkflow, StructuredWorkflow
from orchestrators import ConfigurableOrchestrator
from strategies import MonolithicStrategy, IterativeStrategy, HierarchicalStrategy
from tools.registry import ToolRegistry
from utils.prompt import PromptUtils
from utils.metric import MetricUtils
from utils.workflow import WorkflowUtils

# ---------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------

def _strategy_factory(name: str):
    mapping = {
        "monolithic": MonolithicStrategy,
        "iterative": IterativeStrategy,
        "hierarchical": HierarchicalStrategy,
    }
    cls = mapping.get(name.lower())
    if cls is None:
        raise ValueError(f"Unknown strategy '{name}'. Valid: {', '.join(mapping.keys())}")
    return cls()

def _response_model_factory(name: str):
    mapping = {
        "linear": LinearWorkflow,
        "structured": StructuredWorkflow,
    }
    cls = mapping.get(name.lower())
    if cls is None:
        raise ValueError(f"Unknown response model '{name}'. Valid: {', '.join(mapping.keys())}")
    return cls

def _tools_factory(args):
    if args.no_tools:
        return []
    
    all_tools = ToolRegistry.get_all()

    if not args.tools:
        return all_tools
    
    selected_tools = []
    for tool_name in args.tools:
        tool = ToolRegistry.get(tool_name)
        selected_tools.append(tool)

    return selected_tools

def _features_factory(args):
    selected_features = []
    if args.chat_clarification:
        selected_features.append(ChatClarificationFeature())
    if args.refinement:
        selected_features.append(RefinementFeature())
    return selected_features

# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    # Argument parsing
    argparser = argparse.ArgumentParser(description="AI Workflow Orchestrator")

    # Core run settings
    argparser.add_argument("--runs", type=int, default=1, help="Number of sequential runs to execute (default: 1)")
    argparser.add_argument("--it", action="store_true", help="Pick a random iteration for user prompt")
    argparser.add_argument("--prompt", type=str, default="weather_activity_plan", help="User prompt name to use")
    argparser.add_argument("--execute", action="store_true", help="Whether to execute the generated / loaded workflow")

    # Generation vs loading
    argparser.add_argument("--generate", action="store_true", help="Generate a workflow from the prompt (if not set, the workflow_path will be loaded)")
    argparser.add_argument("--workflow-path", type=str, help="Path to a saved workflow JSON to load when not generating")

    # Strategy & response model
    argparser.add_argument("--strategy", type=str, choices=["monolithic", "iterative", "hierarchical"], default="monolithic",
                            help="Which orchestration strategy to use (default: monolithic)")
    argparser.add_argument("--response-model", type=str, choices=["linear", "structured"], default="linear",
                            help="Which workflow class to use for generation / loading (default: linear)")

    # Features (flags)
    argparser.add_argument("--chat-clarification", action="store_true", help="Enable ChatClarificationFeature")
    argparser.add_argument("--refinement", action="store_true", help="Enable RefinementFeature")

    # Tools
    argparser.add_argument("--tools", nargs="+", help="Subset of tools to enable (by name)")
    argparser.add_argument("--no-tools", action="store_true", help="Disable all tools")

    # Reporting
    argparser.add_argument("--display-metrics", action="store_true", help="Display metrics after each run")

    args = argparser.parse_args()

    # Validate workflow path when loading
    if not args.generate:
        try:
            workflow_path = Path(args.workflow_path)
            if not workflow_path.exists():
                raise FileNotFoundError(f"Workflow path '{workflow_path}' does not exist.")
        except:
            raise ValueError("When not generating a workflow, --workflow-path must be provided and point to a valid file.")

    # Prepare orchestrator components
    strategy_instance = _strategy_factory(args.strategy)
    response_model_cls = _response_model_factory(args.response_model)
    available_tools = _tools_factory(args)
    selected_features = _features_factory(args)

    iterations_idx = []
    formatted_metrics = []
    for run in range(args.runs):
        print(f"\n{'='*40}\nRun {run + 1} of {args.runs}\n{'='*40}\n")

        # Reset metrics before each run
        MetricUtils.reset()

        # Configure the orchestrator with chosen strategy and tools
        orchestrator = ConfigurableOrchestrator(
            strategy=strategy_instance,
            available_tools=available_tools,
            features=selected_features
        )

        # Define the user prompt to use for workflow generation
        if args.it:
            prompts = PromptUtils.get_user_prompts(args.prompt)
            random_idx = random.choice([i for i in range(1, len(prompts) + 1) if i not in iterations_idx])
            iterations_idx.append(random_idx)
            user_prompt = prompts.get(str(random_idx), "1")
        else:
            user_prompt = PromptUtils.get_user_prompts(args.prompt).get("1")

        # Generate or load the workflow
        if args.generate:
            workflow = orchestrator.generate(user_prompt=user_prompt, response_model=response_model_cls)
        else:
            workflow = WorkflowUtils.load_workflow(str(workflow_path), response_model_cls)

        # Execute the workflow (if requested)
        if args.execute:
            orchestrator.run(workflow)

        # Display metrics (if requested)
        if args.display_metrics:
            formatted_metrics.append(MetricUtils.display())
    
    if args.display_metrics:
        MetricUtils.display_formatted_metrics(formatted_metrics)

if __name__ == "__main__":
    main()

