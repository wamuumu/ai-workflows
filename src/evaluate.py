from models import LinearWorkflow, StructuredWorkflow
from utils.workflow import WorkflowUtils
from utils.metric import MetricUtils

# Retrieve workflows to compare
workflow1 = WorkflowUtils.load_json("/path/to/workflow1.json", StructuredWorkflow)
workflow2 = WorkflowUtils.load_json("/path/to/workflow2.json", StructuredWorkflow)

# Compute similarity scores between the two workflows
MetricUtils.similarity_scores(workflow1, workflow2)

# Compute correctness scores against reference constraints
MetricUtils.correctness_scores(
    reference="/path/to/constraints.json",
    workflow=WorkflowUtils.load_json("/path/to/workflow.json", StructuredWorkflow)
)