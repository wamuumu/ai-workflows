# from agents.google import GeminiAgent, GeminiModel
from agents.cerebras import CerebrasAgent, CerebrasModel
from models.linear_workflow import LinearWorkflow
from orchestrators.one_shot import OneShotOrchestrator
from utils.prompt import PromptUtils
from utils.metric import MetricUtils
# from utils.workflow import WorkflowUtils

# Intialize the orchestrator with the desired LLM agent
orchestrator = OneShotOrchestrator({
    "generator": CerebrasAgent(model_name=CerebrasModel.LLAMA_3_3),
    "executor": CerebrasAgent(model_name=CerebrasModel.LLAMA_3_3)
}, skip_execution=True)

# Define the user prompt to use for workflow generation
user_prompt = PromptUtils.get_user_prompt("weather_activity_plan")

# Generate the workflow (one-shot) or load it from a JSON file
# workflow = WorkflowUtils.load_json(json_path, LinearWorkflow)
workflow = orchestrator.generate(user_prompt, response_model=LinearWorkflow, save=False, debug=True)

# Execute the workflow 
orchestrator.run(workflow, debug=True)

# Display metrics
MetricUtils.display()