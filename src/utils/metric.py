import json
import numpy as np

from typing import List
from pydantic import BaseModel, Field
from dataclasses import dataclass
from collections import Counter

@dataclass
class StepMatch:
    step_a_id: str
    step_b_id: str
    similarity: float

class MetricSet(BaseModel):
    time_taken: float = 0
    number_of_calls: int = 0 
    total_tokens: int = 0 # input + output tokens

class MetricSchema(BaseModel):
    generation: MetricSet = Field(default_factory=MetricSet)
    chat: MetricSet = Field(default_factory=MetricSet)
    execution: MetricSet = Field(default_factory=MetricSet)

class MetricUtils:
    
    _metrics: MetricSchema = MetricSchema()
    _has_finished: bool = False

    # ============================= Runtime Metrics ============================= # 

    @classmethod
    def update(cls, category: str, start_time: float, end_time: float, tokens: int) -> None:

        fields = MetricSchema.model_fields

        if category not in fields:
            raise ValueError(f"Invalid metric type: {category}. Valid types are: {list(fields.keys())}")
        
        metric_set: MetricSet = getattr(cls._metrics, category)
        metric_set.time_taken += end_time - start_time
        metric_set.number_of_calls += 1
        metric_set.total_tokens += tokens
    
    @classmethod
    def finish(cls) -> None:
        cls._has_finished = True

    @classmethod
    def display(cls) -> None:
        print("\nOrchestrator Metrics:")
        dumped_metrics = cls._metrics.model_dump()
        for phase, metrics in dumped_metrics.items():
            print(f"  {phase.capitalize()}:")
            for metric_name, value in metrics.items():
                if metric_name == "time_taken":
                    print(f"    {metric_name.replace('_', ' ').capitalize()}: {value:.2f} seconds")
                else:
                    print(f"    {metric_name.replace('_', ' ').capitalize()}: {value}")
        print(f"    Execution finished: {cls._has_finished}\n")
    
    @classmethod
    def reset(cls) -> None:
        """Reset metrics for a new run."""
        cls._metrics = MetricSchema()
    

    # ============================ Evaluation Metrics ============================ #

    # ============================================================================ #
    # 1. Similarity Scores
    # For consistency and reproducibility evaluations
    # ============================================================================ #

    @classmethod
    def similarity_scores(cls, workflows: List[BaseModel], threshold: float = 0.5) -> None:
        """
        Compute pairwise similarity matrix between multiple workflows.
        """
        n = len(workflows)
        matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(i, n):
                total_score = cls._workflow_similarity(workflows[i], workflows[j], threshold)
                matrix[i, j] = total_score
                matrix[j, i] = total_score  # symmetric

        cls._print_similarity_matrix(matrix)
    
    @classmethod
    def _print_similarity_matrix(cls, matrix: np.ndarray):
        n = matrix.shape[0]
        col_width = 6  # width for each column

        # Print header
        header = " " * (col_width - 1) + "".join([f"W{i+1}".ljust(col_width) for i in range(n)])
        print("\nWorkflow Similarity Matrix\n")
        print(header)

        # Print each row
        for i in range(n):
            row_values = "".join([f"{matrix[i, j]:.2f}".ljust(col_width) for j in range(n)])
            print(f"W{i+1}".ljust(col_width - 1) + row_values)

    @classmethod
    def _workflow_similarity(cls, a: BaseModel, b: BaseModel, threshold: float = 0.5) -> float:
        """
        Compute overall similarity between two workflows.
        """
        _, _, _, step_score = cls._align_steps_with_matches(a.steps, b.steps, threshold)
        transition_score = cls._transition_similarity(a, b)

        total_score = 0.7 * step_score + 0.3 * transition_score
        return total_score

    @classmethod
    def _normalize_step(cls, step: BaseModel) -> dict:
        data = step.model_dump()

        return {
            "action": data.get("action"),
            "tool_name": data.get("tool_name"),
            "parameter_keys": sorted(
                p["key"] for p in data.get("parameters") or []
                if "key" in p
            ),
            "is_final": data.get("is_final", False),
        }

    @classmethod
    def _step_similarity(cls, a: BaseModel, b: BaseModel) -> float:
        na, nb = cls._normalize_step(a), cls._normalize_step(b)

        score = 0.0
        weight = 0.0

        def match(x, y):
            return 1.0 if x == y else 0.0

        score += 2.0 * match(na["action"], nb["action"])
        weight += 2.0

        score += 2.0 * match(na["tool_name"], nb["tool_name"])
        weight += 2.0

        a_keys, b_keys = set(na["parameter_keys"]), set(nb["parameter_keys"])
        if a_keys or b_keys:
            score += len(a_keys & b_keys) / len(a_keys | b_keys)
            weight += 1.0

        score += 1.0 * match(na["is_final"], nb["is_final"])
        weight += 1.0

        return score / weight if weight else 0.0

    @classmethod
    def _align_steps_with_matches(cls, steps_a: list[BaseModel], steps_b: list[BaseModel], threshold: float = 0.5):
        used_b = set()
        matches: list[StepMatch] = []
        total_score = 0.0

        for step_a in steps_a:
            best_score = 0.0
            best_j = None

            for j, step_b in enumerate(steps_b):
                if j in used_b:
                    continue

                s = cls._step_similarity(step_a, step_b)
                if s > best_score:
                    best_score = s
                    best_j = j

            if best_j is not None and best_score >= threshold:
                used_b.add(best_j)
                matches.append(
                    StepMatch(
                        step_a_id=step_a.id,
                        step_b_id=steps_b[best_j].id,
                        similarity=best_score,
                    )
                )
                total_score += best_score

        unmatched_a = {s.id for s in steps_a} - {m.step_a_id for m in matches}
        unmatched_b = {s.id for i, s in enumerate(steps_b) if i not in used_b}

        avg_score = total_score / max(len(steps_a), len(steps_b)) if steps_a or steps_b else 0.0

        return matches, unmatched_a, unmatched_b, avg_score

    @classmethod
    def _transition_edges(cls, workflow: BaseModel) -> set[tuple[str, str]]:
        edges = set()

        for step in getattr(workflow, "steps", []):
            transitions = getattr(step, "transitions", None)
            if not transitions:
                continue

            for t in transitions:
                edges.add((step.id, t.next_step))

        return edges

    @classmethod
    def _transition_similarity(cls, a: BaseModel, b: BaseModel) -> float:
        ea = cls._transition_edges(a)
        eb = cls._transition_edges(b)

        if not ea and not eb:
            return 1.0  # linear workflows
        if not ea or not eb:
            return 0.0

        return len(ea & eb) / len(ea | eb)
    
    # ============================================================================ #
    # 2. Correctness Scores
    # For expected behavior evaluations
    # ============================================================================ #

    @classmethod
    def correctness_scores(cls, reference: str, workflow: BaseModel) -> None:

        with open(reference, "r") as ref:
            reference_data = json.load(ref)
        
        # Expected tool calls
        tool_count = Counter(step.tool_name for step in workflow.steps if step.action == "call_tool" and step.tool_name)
        expected_tool_calls = reference_data.get("expected_tool_calls", {})

        tool_scores = []
        for tool, limits in expected_tool_calls.items(): 
            count = tool_count.get(tool, 0)
            tool_scores.append(cls._action_score(count, limits["min"], limits["max"]))

        # Expected LLM calls
        llm_count = sum(1 for step in workflow.steps if step.action == "call_llm")
        expected_llm_calls = reference_data.get("expected_llm_calls", {})
        llm_score = cls._action_score(llm_count, expected_llm_calls.get("min", 0), expected_llm_calls.get("max", float('inf')))

        # Expected total steps
        total_steps = len(workflow.steps)
        expected_total_steps = reference_data.get("expected_step_count_range", [])
        if total_steps >= expected_total_steps[0] and total_steps <= expected_total_steps[1]:
            step_score = 1

        # Expected branch transitions
        transition_score = 0
        branching_nodes = [step for step in workflow.steps if step.transitions and len(step.transitions) > 1]
        expected_branching = reference_data.get("expected_branch_transitions", {})
        for _ , constraints in expected_branching.items():
            keywords = constraints.get("keywords", [])
            for step in branching_nodes:
                if any(kw in step.parameters[0].value for kw in keywords):
                    branch_count = len(step.transitions)
                    if constraints.get("transitions", 0) == branch_count:
                        transition_score += 1
        
        transition_score = transition_score / max(len(branching_nodes), 1)

        # Aggregate scores
        all_scores = tool_scores + [llm_score, step_score, transition_score]
        overall_score = sum(all_scores) / len(all_scores) if all_scores else 0

        # Print summary
        print("\nCorrectness Evaluation Results:")
        print(f"  Overall correctness score: {overall_score:.3f}")
        print(f"  Tool call scores: {[f'{s:.3f}' for s in tool_scores]}")
        print(f"  LLM call score: {llm_score:.3f}")
        print(f"  Total step score: {step_score:.3f}")
        print(f"  Branch transition score: {transition_score:.3f}\n")

    @classmethod
    def _action_score(cls, count: int, min_calls: int, max_calls: int) -> float:
        if count < min_calls:
            return count / min_calls
        elif count > max_calls:
            return max_calls / count
        else:
            return 1.0