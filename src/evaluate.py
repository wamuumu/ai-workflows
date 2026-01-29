import argparse

from utils.workflow import WorkflowUtils, EXECUTIONS, WORKFLOWS
from utils.metric import MetricUtils
from pathlib import Path

def main():

    # Argument parsing
    argparser = argparse.ArgumentParser(description="AI Workflow Validator")

    argparser.add_argument("--reference", type=str, help="Path to the reference constraints JSON file")
    argparser.add_argument("--workflow-similarity", action="store_true", help="Compute similarity scores between workflows")
    argparser.add_argument("--execution-similarity", action="store_true", help="Compute similarity scores between executions")
    argparser.add_argument("--correctness-scores", action="store_true", help="Compute correctness scores against reference constraints")
    argparser.add_argument("--intent-resolution", action="store_true", help="Compute intent resolution scores for workflows")
    argparser.add_argument("--reasoning-coherence", action="store_true", help="Compute reasoning coherence scores for workflows")
    argparser.add_argument("--all", action="store_true", help="Compute all metrics")
    
    args = argparser.parse_args()

    if args.all:
        args.workflow_similarity = True
        args.execution_similarity = True
        args.correctness_scores = True
        args.intent_resolution = True
        args.reasoning_coherence = True
    
    # Retrieve workflows to compare
    workflows = []
    workflow_files = sorted(Path(WORKFLOWS).glob("workflow_*.json"), key=lambda x: int(x.stem.split('_')[-1]))
    for i, file in enumerate(workflow_files):
        workflows.append(WorkflowUtils.load_workflow(str(file)))
        print(f"Loaded workflow {i+1} from {file}")

    # Compute similarity matrix between workflows
    if args.workflow_similarity and workflows:
        MetricUtils.similarity_scores(workflows)
    else:
        print("Skipping workflow similarities...\n")

    executions = []
    execution_files = sorted(Path(EXECUTIONS).glob("execution_*.json"), key=lambda x: int(x.stem.split('_')[-1]))
    for i, file in enumerate(execution_files):
        executions.append(WorkflowUtils.load_execution(str(file)))
        print(f"Loaded execution {i+1} from {file}")

    # Compute execution similarity score
    if args.execution_similarity and executions:
        MetricUtils.execution_similarity_scores(executions)
    else:
        print("Skipping execution similarities...\n")

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
    else:
        print("Skipping correctness scores...\n")
    
    if args.intent_resolution and workflows:
        MetricUtils.intent_resolution_scores(workflows=workflows)
    else:
        print("Skipping intent resolution scores...\n")

    if args.reasoning_coherence and workflows:
        MetricUtils.reasoning_coherence_scores(workflows=workflows)
    else:
        print("Skipping reasoning coherence scores...\n")

if __name__ == "__main__":
    main()