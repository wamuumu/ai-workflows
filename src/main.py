import argparse

from agents.google import GeminiAgent, GeminiModel
from agents.cerebras import CerebrasAgent, CerebrasModel
from features import ChatClarificationFeature, RefinementFeature
from models import LinearWorkflow, StructuredWorkflow
from orchestrators import ConfigurableOrchestrator
from strategies import MonolithicStrategy, IterativeStrategy
from utils.prompt import PromptUtils
from utils.metric import MetricUtils

argparser = argparse.ArgumentParser(description="AI Workflow Orchestrator")
argparser.add_argument("--runs", type=int, default=1, help="Number of sequential runs to execute")
args = argparser.parse_args()

for run in range(args.runs):
    print(f"\n{'='*40}\nRun {run + 1} of {args.runs}\n{'='*40}\n")

    # Reset metrics before each run
    MetricUtils.reset()
    
    # Configure the orchestrator with desired agents, strategy and features
    orchestrator = ConfigurableOrchestrator(
        strategy=MonolithicStrategy(),
        features=[ChatClarificationFeature()],
    )

    # Define the user prompt to use for workflow generation
    user_prompt = PromptUtils.get_user_prompt("weather_activity_plan")

    # Generate the workflow (one-shot)
    workflow = orchestrator.generate(user_prompt, response_model=StructuredWorkflow, save=False, debug=True)

    # Execute the workflow
    if False: 
        orchestrator.run(workflow, debug=True)

    # Display metrics
    MetricUtils.display()