from agents.google import GeminiAgent, GeminiModel
from agents.cerebras import CerebrasAgent, CerebrasModel
from models.structured_workflow import StructuredWorkflow
from orchestrators.chat_driven import ChatDrivenOrchestrator
from utils.prompt import PromptUtils
from utils.metric import MetricUtils
# from utils.workflow import WorkflowUtils

# Initialize the orchestrator
orchestrator = ChatDrivenOrchestrator({
    "generator": CerebrasAgent(model_name=CerebrasModel.LLAMA_3_3),
    "chatter": GeminiAgent(model_name=GeminiModel.GEMINI_2_5_FLASH),
    "executor": CerebrasAgent(model_name=CerebrasModel.LLAMA_3_3)
}, skip_execution=True)

# Define the user prompt to use for workflow generation
user_prompt = PromptUtils.get_user_prompt("weather_activity_plan")

# Generate the workflow (chat-based with clarification) or load it from a JSON file
# workflow = WorkflowUtils.load_json(json_path, StructuredWorkflow)
workflow = orchestrator.generate(user_prompt, response_model=StructuredWorkflow, save=False, debug=True)

# Execute the workflow
orchestrator.run(workflow, debug=True)

# Display metrics
MetricUtils.display()