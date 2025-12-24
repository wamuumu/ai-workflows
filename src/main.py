import argparse
import random

from agents.google import GeminiAgent, GeminiModel
from agents.cerebras import CerebrasAgent, CerebrasModel
from features import ChatClarificationFeature, RefinementFeature
from models import LinearWorkflow, StructuredWorkflow
from orchestrators import ConfigurableOrchestrator
from strategies import MonolithicStrategy, IterativeStrategy, HierarchicalStrategy
from utils.prompt import PromptUtils
from utils.metric import MetricUtils

iterations_idx = []

argparser = argparse.ArgumentParser(description="AI Workflow Orchestrator")
argparser.add_argument("--runs", type=int, default=1, help="Number of sequential runs to execute")
argparser.add_argument("--it", type=bool, default=False, help="Pick a random iteration for user prompt")
args = argparser.parse_args()

for run in range(args.runs):
    print(f"\n{'='*40}\nRun {run + 1} of {args.runs}\n{'='*40}\n")

    # Reset metrics before each run
    MetricUtils.reset()
    
    # Configure the orchestrator with desired agents, strategy and features
    orchestrator = ConfigurableOrchestrator(
        strategy=MonolithicStrategy()
    )

    # Define the user prompt to use for workflow generation
    if args.it:
        # Pick random iteration index not already picked
        prompts = PromptUtils.get_user_prompts("weather_activity_plan")
        random_idx = random.choice([i for i in range(1, len(prompts)+1) if i not in iterations_idx])
        iterations_idx.append(random_idx)
        user_prompt = prompts.get(str(random_idx), "1")
    else:
        user_prompt = PromptUtils.get_user_prompts("weather_activity_plan").get("1")

    # Generate the workflow (one-shot)
    workflow = orchestrator.generate(user_prompt, response_model=StructuredWorkflow, save=True, debug=False)

    # Execute the workflow
    if False: 
        orchestrator.run(workflow, debug=True)

    # Display metrics
    MetricUtils.display()