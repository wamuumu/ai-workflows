from agents.google import GeminiAgent, GeminiModel
from agents.cerebras import CerebrasAgent, CerebrasModel
from models.structured_workflow import StructuredWorkflow
from orchestrators.hierarchical import HierarchicalOrchestrator
from utils.prompt import PromptUtils
# from utils.workflow import WorkflowUtils

# Initialize the orchestrator
orchestrator = HierarchicalOrchestrator({
    "planner": CerebrasAgent(model_name=CerebrasModel.LLAMA_3_3),
    "generator": CerebrasAgent(model_name=CerebrasModel.LLAMA_3_3),
    "executor": GeminiAgent(model_name=GeminiModel.GEMINI_2_5_FLASH)
})

# Define the user prompt to use for workflow generation
user_prompt = PromptUtils.get_user_prompt("weather_activity_plan")

# Generate the workflow (hierarchical) or load it from a JSON file
workflow = orchestrator.generate(user_prompt, response_model=StructuredWorkflow, save=False, debug=True)

# Execute the workflow 
orchestrator.run(workflow, debug=True)