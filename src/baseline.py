import argparse

from agents.google import GeminiAgent, GeminiModel
from agents.cerebras import CerebrasAgent, CerebrasModel
from models.linear_workflow import LinearWorkflow
from orchestrators.one_shot import OneShotOrchestrator
from utils.prompt import PromptUtils
from utils.metric import MetricUtils

argparser = argparse.ArgumentParser(description="AI Workflow One-Shot Orchestrator")
argparser.add_argument("--runs", type=int, default=1, help="Number of runs to execute")
args = argparser.parse_args()

for run in range(args.runs):
    print(f"\n--- Run {run + 1} of {args.runs} ---\n")
    
    # Intialize the orchestrator with the desired LLM agent
    orchestrator = OneShotOrchestrator({
        "generator": GeminiAgent(model_name=GeminiModel.GEMINI_2_5_FLASH),
        "executor": CerebrasAgent(model_name=CerebrasModel.LLAMA_3_3)
    }, skip_execution=True)

    # Define the user prompt to use for workflow generation
    user_prompt = PromptUtils.get_user_prompt("weather_activity_plan")

    # Generate the workflow (one-shot)
    workflow = orchestrator.generate(user_prompt, response_model=LinearWorkflow, save=False, debug=True)

    # Execute the workflow 
    orchestrator.run(workflow, debug=True)

    # Display metrics
    MetricUtils.display()