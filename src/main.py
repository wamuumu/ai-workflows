import argparse
import random

from features import ChatClarificationFeature, RefinementFeature, ValidationRefinementFeature
from models.workflows import LinearWorkflow, StructuredWorkflow
from orchestrators import ConfigurableOrchestrator
from strategies import MonolithicStrategy, IncrementalStrategy, BottomUpStrategy
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
        "incremental": IncrementalStrategy,
        "bottomup": BottomUpStrategy
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
    if args.validation_refinement:
        selected_features.append(ValidationRefinementFeature())
    return selected_features

# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    # Argument parsing
    argparser = argparse.ArgumentParser(description="AI Workflow Orchestrator")

    # =========================================================
    # Core Settings
    # =========================================================
    argparser.add_argument("--runs", type=int, default=1, help="Number of sequential runs to execute (default: 1)")
    argparser.add_argument("--it", action="store_true", help="Pick a random iteration for prompt (generate) or workflow (execute)")

    # =========================================================
    # Generation Settings
    # =========================================================
    argparser.add_argument("--generate", action="store_true", help="Generate a workflow from the given prompt")
    argparser.add_argument("--prompt", type=str, default="weather_activity_plan", help="User prompt name to use")

    # Strategy & response model
    argparser.add_argument("--strategy", type=str, choices=["monolithic", "incremental", "bottomup"], default="monolithic",
                            help="Which orchestration strategy to use (default: monolithic)")
    argparser.add_argument("--response-model", type=str, choices=["linear", "structured"], default="structured",
                            help="Which workflow class to use for generation / loading (default: structured)")

    # Features (flags)
    argparser.add_argument("--chat-clarification", action="store_true", help="Enable ChatClarificationFeature")
    argparser.add_argument("--refinement", action="store_true", help="Enable RefinementFeature")
    argparser.add_argument("--validation-refinement", action="store_true", help="Enable ValidationRefinementFeature")

    # Tools
    argparser.add_argument("--tools", nargs="+", help="Subset of tools to enable (by name)")
    argparser.add_argument("--no-tools", action="store_true", help="Disable all tools")

    # =========================================================
    # Execution Settings
    # =========================================================
    argparser.add_argument("--execute", action="store_true", help="Execute the generated or loaded workflow")
    argparser.add_argument("--workflow-path", type=str, help="Path to a saved workflow JSON to load when not generating")

    # =========================================================
    # Reporting Settings
    # =========================================================
    argparser.add_argument("--display-metrics", action="store_true", help="Display metrics after each run")

    args = argparser.parse_args()

    # Prepare orchestrator components
    strategy_instance = _strategy_factory(args.strategy)
    response_model_cls = _response_model_factory(args.response_model)
    available_tools = _tools_factory(args)
    selected_features = _features_factory(args)

    random_idx = -1
    iterations_idx = []
    formatted_metrics = []
    for run in range(args.runs):
        print(f"\n{'='*40}\nRun {run + 1} of {args.runs}\n{'='*40}\n")

        # Reset metrics and random seed between runs
        MetricUtils.reset()
        random.seed(run)

        # Configure the orchestrator with chosen strategy and tools
        orchestrator = ConfigurableOrchestrator(
            strategy=strategy_instance,
            available_tools=available_tools,
            features=selected_features
        )

        # Determine the user intention
        if args.generate:
                
            prompts = PromptUtils.get_user_prompts(args.prompt)
            
            if args.it:
                random_idx = random.choice([i for i in range(1, len(prompts) + 1) if i not in iterations_idx])
                iterations_idx.append(random_idx)
            else:
                random_idx = 1  # Default to the first prompt

            # Pick the random prompt for this iteration
            user_prompt = prompts.get(str(random_idx))

            print(f"User Prompt (iteration {random_idx}): {user_prompt}\n")

            # Generate the workflow
            workflow = orchestrator.generate(user_prompt=user_prompt, response_model=response_model_cls, debug=False)

            # If also executing, run it 
            if args.execute:
                orchestrator.run(workflow)  
            
        elif args.execute:
            
            workflow_files = WorkflowUtils.list_workflows()
            
            if args.workflow_path:
                workflow_path = args.workflow_path
            elif args.it:
                random_idx = random.choice([i for i in range(0, len(workflow_files)) if i not in iterations_idx])
                iterations_idx.append(random_idx)
                workflow_path = workflow_files[random_idx]
            else:
                workflow_path = workflow_files[0] # Pick the first one by default
            
            print(f"Workflow: {workflow_path}\n")
                
            # Load the workflow
            workflow = WorkflowUtils.load_workflow(str(workflow_path), response_model_cls)
            
            # Execute the workflow
            orchestrator.run(workflow)
        else:
            raise ValueError("At least one of --generate or --execute must be specified.")

        # Display metrics (if requested)
        if args.display_metrics:
            formatted_metrics.append(MetricUtils.display())
    
    if args.display_metrics:
        MetricUtils.display_formatted_metrics(formatted_metrics)

if __name__ == "__main__":
    main()

