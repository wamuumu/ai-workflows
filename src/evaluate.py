import argparse

from models import LinearWorkflow, StructuredWorkflow
from utils.workflow import WorkflowUtils, EXECUTIONS, WORKFLOWS
from utils.metric import MetricUtils
from pathlib import Path

def _response_model_factory(name: str):
    mapping = {
        "linear": LinearWorkflow,
        "structured": StructuredWorkflow,
    }
    cls = mapping.get(name.lower())
    if cls is None:
        raise ValueError(f"Unknown response model '{name}'. Valid: {', '.join(mapping.keys())}")
    return cls

def main():

    # Argument parsing
    argparser = argparse.ArgumentParser(description="AI Workflow Validator")

    argparser.add_argument("--reference", type=str, help="Path to the reference constraints JSON file")
    argparser.add_argument("--response-model", type=str, choices=["linear", "structured"], default="structured",
                            help="Which workflow class to use for validation (default: structured)")
    argparser.add_argument("--workflow-similarity", action="store_true", help="Compute similarity scores between workflows")
    argparser.add_argument("--execution-similarity", action="store_true", help="Compute similarity scores between executions")
    argparser.add_argument("--correctness-scores", action="store_true", help="Compute correctness scores against reference constraints")
    argparser.add_argument("--all", action="store_true", help="Compute all metrics")
    
    args = argparser.parse_args()

    if args.all:
        args.workflow_similarity = True
        args.execution_similarity = True
        args.correctness_scores = True

    response_model_cls = _response_model_factory(args.response_model)
    
    # Retrieve workflows to compare
    workflows = []
    if args.workflow_similarity or args.correctness_scores:
        workflow_files = sorted(Path(WORKFLOWS).glob("workflow_*.json"))
        for i, file in enumerate(workflow_files):
            workflows.append(WorkflowUtils.load_workflow(str(file), response_model_cls))
            print(f"Loaded workflow {i+1} from {file}")

    # Compute similarity matrix between workflows
    if args.workflow_similarity and workflows:
        MetricUtils.similarity_scores(workflows)

    executions = []
    if args.execution_similarity:
        execution_files = sorted(Path(EXECUTIONS).glob("execution_*.json"))
        for i, file in enumerate(execution_files):
            executions.append(WorkflowUtils.load_execution(str(file)))
            print(f"Loaded execution {i+1} from {file}")

    # Compute execution similarity score
    if args.execution_similarity and executions:
        MetricUtils.execution_similarity_scores(executions)

    # Compute correctness scores against reference constraints
    if args.reference:
        try:
            reference_path = Path(args.reference)
            if not reference_path.exists():
                raise FileNotFoundError(f"Reference path '{reference_path}' does not exist.")
        except:
            raise ValueError("A valid reference path must be provided for correctness scoring.")
        
        if args.correctness_scores and workflows:
            MetricUtils.correctness_scores(
                reference=str(reference_path),
                workflows=workflows
            )

if __name__ == "__main__":
    main()