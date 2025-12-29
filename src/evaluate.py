from models import LinearWorkflow, StructuredWorkflow
from utils.workflow import WorkflowUtils, EXECUTIONS, WORKFLOWS
from utils.metric import MetricUtils
from pathlib import Path

# Retrieve workflows to compare
workflows = []
workflow_files = sorted(Path(WORKFLOWS).glob("workflow_*.json"))
for i, file in enumerate(workflow_files):
    print(f"Loading workflow {i+1} from {file}")
    workflows.append(WorkflowUtils.load_workflow(str(file), LinearWorkflow))

# Compute similarity matrix between workflows
MetricUtils.similarity_scores(workflows)

executions = []
execution_files = sorted(Path(EXECUTIONS).glob("execution_*.json"))
for file in execution_files:
    executions.append(WorkflowUtils.load_execution(str(file)))

# Compute execution similarity score
MetricUtils.execution_similarity_scores(executions)

exit(0)

# Compute correctness scores against reference constraints
MetricUtils.correctness_scores(
    reference="/path/to/constraints.json",
    workflow=WorkflowUtils.load_workflow("/path/to/workflow.json", StructuredWorkflow)
)