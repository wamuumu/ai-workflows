import argparse
import random

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

iterations_idx = []

argparser = argparse.ArgumentParser(description="AI Workflow Orchestrator")
argparser.add_argument("--runs", type=int, default=1, help="Number of sequential runs to execute")
argparser.add_argument("--it", type=bool, default=False, help="Pick a random iteration for user prompt")
argparser.add_argument("--prompt", type=str, default="weather_activity_plan", help="User prompt name to use")
argparser.add_argument("--execute", type=bool, default=False, help="Whether to execute the generated workflow")
args = argparser.parse_args()

#TODO: make all configurable via args

for run in range(args.runs):
    print(f"\n{'='*40}\nRun {run + 1} of {args.runs}\n{'='*40}\n")

    # Reset metrics before each run
    MetricUtils.reset()
    
    # Configure the orchestrator with desired agents, strategy and features
    orchestrator = ConfigurableOrchestrator(
        strategy=MonolithicStrategy(),
        available_tools=ToolRegistry.get_all()
    )

    # Define the user prompt to use for workflow generation
    if args.it:
        # Pick random iteration index not already picked
        prompts = PromptUtils.get_user_prompts(args.prompt)
        random_idx = random.choice([i for i in range(1, len(prompts)+1) if i not in iterations_idx])
        iterations_idx.append(random_idx)
        user_prompt = prompts.get(str(random_idx), "1")
    else:
        user_prompt = PromptUtils.get_user_prompts(args.prompt).get("1")

    # Generate the workflow
    # workflow = orchestrator.generate(user_prompt, response_model=LinearWorkflow)
    workflow_test = WorkflowUtils.load_workflow("/home/wamuumu/ai-workflows/data/workflows/workflow_20251229_183941_1f660b13bbe54d84b1eae631e52dd9c8.json", LinearWorkflow)

    # Execute the workflow
    if args.execute: 
        orchestrator.run(workflow_test)

    # Display metrics
    MetricUtils.display()