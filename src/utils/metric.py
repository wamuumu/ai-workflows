from pydantic import BaseModel, Field
from dataclasses import dataclass

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
    
    @classmethod
    def reset(cls) -> None:
        """Reset metrics for a new run."""
        cls._metrics = MetricSchema()
    

    # ============================ Evaluation Metrics ============================ #

    # Workflow Similarity Scores

    @classmethod
    def similarity_scores(cls, a: BaseModel, b: BaseModel) -> None:
        matches, unmatched_a, unmatched_b, step_score = cls._align_steps_with_matches(
            a.steps, b.steps
        )

        transition_score = cls._transition_similarity(a, b)

        total_score = (
            0.7 * step_score +
            0.3 * transition_score
        )

        # Print summary
        print("\nWorkflow Comparison Results:")
        print(f"  Total similarity: {total_score:.3f}")
        print(f"  Step similarity: {step_score:.3f}")
        print(f"  Transition similarity: {transition_score:.3f}\n")

        # Print matched steps
        print("  Matched steps:")
        for m in matches:
            print(f"    {m.step_a_id} ↔ {m.step_b_id} | similarity: {m.similarity:.3f}")

        # Print unmatched steps
        if unmatched_a:
            print("\nUnmatched steps in first workflow:")
            for s in unmatched_a:
                print(f"  {s}")

        if unmatched_b:
            print("\nUnmatched steps in second workflow:")
            for s in unmatched_b:
                print(f"  {s}")

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
    
    # TODO: Implement others...