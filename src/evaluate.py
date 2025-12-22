from models import LinearWorkflow, StructuredWorkflow
from utils.workflow import WorkflowUtils
from utils.metric import MetricUtils

# Retrieve workflows to compare
workflow1 = WorkflowUtils.load_json("/path/to/workflow1.json", StructuredWorkflow)
workflow2 = WorkflowUtils.load_json("/path/to/workflow2.json", StructuredWorkflow)

# Compute similarity scores between the two workflows
MetricUtils.similarity_scores(workflow1, workflow2)