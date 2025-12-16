import argparse

from agents.google import GeminiAgent, GeminiModel
from agents.cerebras import CerebrasAgent, CerebrasModel
from models.structured_workflow import StructuredWorkflow
from orchestrators.two_stage import TwoStageOrchestrator
from utils.prompt import PromptUtils
from utils.metric import MetricUtils

argparser = argparse.ArgumentParser(description="AI Workflow Two-Stage Orchestrator")
argparser.add_argument("--runs", type=int, default=1, help="Number of runs to execute")
args = argparser.parse_args()

for run in range(args.runs):
    print(f"\n--- Run {run + 1} of {args.runs} ---\n")

    # Initialize the orchestrator
    orchestrator = TwoStageOrchestrator({
        "generator": CerebrasAgent(model_name=CerebrasModel.GPT_OSS),
        "refiner": GeminiAgent(model_name=GeminiModel.GEMINI_2_5_FLASH),
        "executor": CerebrasAgent(model_name=CerebrasModel.LLAMA_3_3)
    }, skip_execution=True)

    # Define the user prompt to use for workflow generation
    user_prompt = PromptUtils.get_user_prompt("weather_activity_plan")

    # Generate the workflow (one-shot + refinement)
    workflow = orchestrator.generate(user_prompt, response_model=StructuredWorkflow, save=False, debug=False)

    # Execute the workflow
    orchestrator.run(workflow, debug=True)

    # Display metrics
    MetricUtils.display()