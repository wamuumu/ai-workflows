import os
import json
import numpy as np
import logging

from typing import List, Dict, Any
from pydantic import BaseModel, Field
from dataclasses import dataclass
from collections import Counter
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from utils.logger import LoggerUtils

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) 
LOG_DIR = os.path.join(ROOT, "metrics")

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
    _logger = LoggerUtils(name="MetricLogger", log_dir=LOG_DIR, log_to_console=True)

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
        cls._logger.log(logging.INFO, "Orchestrator Metrics:")
        dumped_metrics = cls._metrics.model_dump()
        for phase, metrics in dumped_metrics.items():
            cls._logger.log(logging.INFO, f"  {phase.capitalize()}:")
            for metric_name, value in metrics.items():
                if metric_name == "time_taken":
                    cls._logger.log(logging.INFO, f"    {metric_name.replace('_', ' ').capitalize()}: {value:.2f} seconds")
                else:
                    cls._logger.log(logging.INFO, f"    {metric_name.replace('_', ' ').capitalize()}: {value}")
        cls._logger.log(logging.INFO, f"    Execution finished: {cls._has_finished}\n")
    
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

        cls._print_similarity_matrix(matrix, title="Workflow Similarity Matrix")

        # Print additional statistics
        avg_similarity = np.mean(matrix[np.triu_indices_from(matrix, k=1)])
        std_similarity = np.std(matrix[np.triu_indices_from(matrix, k=1)])
        cls._logger.log(logging.INFO, f"Average pairwise similarity: {avg_similarity:.3f}")
        cls._logger.log(logging.INFO, f"Standard deviation: {std_similarity:.3f}")
        cls._logger.log(logging.INFO, f"Min similarity: {np.min(matrix[np.triu_indices_from(matrix, k=1)]):.3f}")
        cls._logger.log(logging.INFO, f"Max similarity: {np.max(matrix[np.triu_indices_from(matrix, k=1)]):.3f}")

        # Return the workflow with highest average similarity
        avg_scores = np.mean(matrix, axis=1)
        best_index = int(np.argmax(avg_scores))
        cls._logger.log(logging.INFO, f"Workflow W{best_index + 1} has the highest average similarity of {avg_scores[best_index]:.3f}\n")
    
    @classmethod
    def _print_similarity_matrix(cls, matrix: np.ndarray, title: str) -> None:
        n = matrix.shape[0]
        col_width = 6  # width for each column

        # Print header
        header = " " * (col_width - 1) + "".join([f"W{i+1}".ljust(col_width) for i in range(n)])
        cls._logger.log(logging.INFO, title)
        cls._logger.log(logging.INFO, header)

        # Print each row
        for i in range(n):
            row_values = "".join([f"{matrix[i, j]:.2f}".ljust(col_width) for j in range(n)])
            cls._logger.log(logging.INFO, f"W{i+1}".ljust(col_width - 1) + row_values)

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
    # 2. Correctness and Resoning / Intent Resolution Scores
    # Against reference specifications
    # ============================================================================ #

    @classmethod
    def correctness_scores(cls, reference: str, workflows: List[BaseModel]) -> None:
        """
        Evaluate correctness of multiple workflows against a reference specification.
        
        Args:
            reference: Path to JSON file with expected behavior specifications
            workflows: List of workflow objects to evaluate
        """
        with open(reference, "r") as ref:
            reference_data = json.load(ref)
        
        embeddings = cls._compute_embeddings(workflows)

        results = []
        for idx, workflow in enumerate(workflows):
            # Expected tool calls
            tool_count = Counter(step.tool_name for step in workflow.steps if step.action == "call_tool" and step.tool_name)
            expected_tool_calls = reference_data.get("expected_tool_calls", {})
        
            tool_scores = []
            for tool, limits in expected_tool_calls.items(): 
                count = tool_count.get(tool, 0)
                min_calls, max_calls = limits.get("min", 0), limits.get("max", float('inf'))
                tool_scores.append(cls._get_score(count, min_calls, max_calls))

            # Expected LLM calls
            llm_count = sum(1 for step in workflow.steps if step.action == "call_llm")
            expected_llm_calls = reference_data.get("expected_llm_calls", {})
            if expected_llm_calls and len(expected_llm_calls) == 2:
                min_calls, max_calls = expected_llm_calls.get("min", 0), expected_llm_calls.get("max", float('inf'))
                llm_score = cls._get_score(llm_count, min_calls, max_calls)
            else:
                llm_score = 0.0

            # Expected total steps
            total_steps = len(workflow.steps)
            expected_total_steps = reference_data.get("expected_step_count_range", [])
            if expected_total_steps and len(expected_total_steps) == 2:
                min_steps, max_steps = expected_total_steps.get("min", 0), expected_total_steps.get("max", float('inf'))
                step_score = cls._get_score(total_steps, min_steps, max_steps)
            else:
                step_score = 0.0

            # Expected branch transitions
            transition_score = 0
            branching_nodes = [step for step in workflow.steps if hasattr(step, "transitions") and len(step.transitions) > 1]
            if branching_nodes:
                expected_branching = reference_data.get("expected_branch_transitions", {})
                for _, constraints in expected_branching.items():
                    keywords = constraints.get("keywords", [])
                    for step in branching_nodes:
                        if any(kw in step.parameters[0].value for kw in keywords):
                            branch_count = len(step.transitions)
                            if constraints.get("transitions", 0) == branch_count:
                                transition_score += 1
            
                transition_score = transition_score / max(len(branching_nodes), 1)
            
            reference_goal = reference_data.get("expected_goal", "")
            reference_thoughts = "\n".join(reference_data.get("expected_thoughts", []))
            goal_score, thoughts_score = cls._embedding_score(embeddings[idx], reference_thoughts, reference_goal)

            # Overall correctness score
            weighted_scores = {
                "tool": 0.40,
                "llm": 0.15,
                "step": 0.25,
                "transition": 0.20
            }

            all_scores = tool_scores + [llm_score, step_score, transition_score]
            overall_score = sum(all_scores) / len(all_scores) if all_scores else 0
            overall_weighted_score = (
                np.mean(tool_scores) * weighted_scores["tool"] + 
                llm_score * weighted_scores["llm"] +
                step_score * weighted_scores["step"] +
                transition_score * weighted_scores["transition"] )

            results.append({
                "workflow_index": idx + 1,
                "overall_score": overall_score,
                "overall_weighted_score": overall_weighted_score,
                "tool_scores": tool_scores,
                "llm_score": llm_score,
                "step_score": step_score,
                "transition_score": transition_score,
                "goal_score": goal_score,
                "thoughts_score": thoughts_score
            })

        # Print summary for all workflows
        cls._logger.log(logging.INFO, "Correctness Evaluation Results:")
        for result in results:
            cls._logger.log(logging.INFO, f"  Workflow W{result['workflow_index']}:")
            cls._logger.log(logging.INFO, f"    Overall correctness score: {result['overall_score']:.3f}")
            cls._logger.log(logging.INFO, f"    Overall weighted correctness score: {result['overall_weighted_score']:.3f}")
            cls._logger.log(logging.INFO, f"    Tool call scores: {[f'{s:.3f}' for s in result['tool_scores']]}")
            cls._logger.log(logging.INFO, f"    Average tool call score: {np.mean(result['tool_scores']):.3f}" if result['tool_scores'] else "    Average tool call score: N/A")
            cls._logger.log(logging.INFO, f"    LLM call score: {result['llm_score']:.3f}")
            cls._logger.log(logging.INFO, f"    Total step score: {result['step_score']:.3f}")
            cls._logger.log(logging.INFO, f"    Branch transition score: {result['transition_score']:.3f}")
            cls._logger.log(logging.INFO, f"    Goal similarity score: {result['goal_score']:.3f}")
            cls._logger.log(logging.INFO, f"    Thoughts similarity score: {result['thoughts_score']:.3f}\n")
        
        # cls._logger.log aggregate statistics
        overall_scores = [r['overall_score'] for r in results]
        cls._logger.log(logging.INFO, f"  Average correctness score: {np.mean(overall_scores):.3f}")
        cls._logger.log(logging.INFO, f"  Min correctness score: {np.min(overall_scores):.3f}")
        cls._logger.log(logging.INFO, f"  Max correctness score: {np.max(overall_scores):.3f}")
        cls._logger.log(logging.INFO, f"  Average goal similarity score: {np.mean([r['goal_score'] for r in results]):.3f}")
        cls._logger.log(logging.INFO, f"  Average thoughts similarity score: {np.mean([r['thoughts_score'] for r in results]):.3f}")
    
    @classmethod
    def _get_score(cls, count: int, min_val: int, max_val: int) -> float:
        if (count >= min_val and count <= max_val):
            return 1.0
        else:
            step_mean = (min_val + max_val) / 2
            distance = min(abs(count - min_val), abs(count - max_val))
            return 1.0 - (distance / step_mean) if step_mean > 0 else 0.0
    
    @classmethod
    def _compute_embeddings(cls, workflows: List[BaseModel]) -> List[np.ndarray]:
        model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        embeddings = []

        for workflow in workflows:
            texts = []
            if hasattr(workflow, "target_objective"):
                texts.append(workflow.target_objective)
            else:
                texts.append("")
            
            thoughts_str = ""
            for step in workflow.steps:
                if hasattr(step, "thoughts"):
                    thoughts_str += "\n" + step.thoughts
            texts.append(thoughts_str)

            emb = model.encode(texts)
            embeddings.append(emb)
        
        return embeddings

    @classmethod
    def _embedding_score(cls, embedding: np.ndarray, ref_thoughts: str, ref_goal: str) -> tuple[float, float]:
        model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')

        ref_thoughts_emb = model.encode([ref_thoughts])
        ref_goal_emb = model.encode([ref_goal])

        goal_sim = max(0, min(1, cosine_similarity([embedding[0]], ref_goal_emb)[0][0]))
        thoughts_sim = max(0, min(1, cosine_similarity([embedding[1]], ref_thoughts_emb)[0][0]))

        return goal_sim, thoughts_sim
    
    # ============================================================================ #
    # 3. Execution Result Similarity Scores
    # For comparing actual execution outputs across multiple runs
    # ============================================================================ #

    @classmethod
    def execution_similarity_scores(cls, execution_results: List[Dict[str, Any]]) -> None:
        """
        Compute pairwise similarity matrix between execution results.
        
        Args:
            execution_results: List of execution result dictionaries, where each dict
                              maps step_id -> step_output
        """
        n = len(execution_results)
        matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(i, n):
                total_score = cls._execution_result_similarity(
                    execution_results[i], 
                    execution_results[j]
                )
                matrix[i, j] = total_score
                matrix[j, i] = total_score

        cls._print_similarity_matrix(matrix, title="Execution Result Similarity Matrix")
        
        # Print additional statistics
        avg_similarity = np.mean(matrix[np.triu_indices_from(matrix, k=1)])
        std_similarity = np.std(matrix[np.triu_indices_from(matrix, k=1)])
        cls._logger.log(logging.INFO, f"Average pairwise similarity: {avg_similarity:.3f}")
        cls._logger.log(logging.INFO, f"Standard deviation: {std_similarity:.3f}")
        cls._logger.log(logging.INFO, f"Min similarity: {np.min(matrix[np.triu_indices_from(matrix, k=1)]):.3f}")
        cls._logger.log(logging.INFO, f"Max similarity: {np.max(matrix[np.triu_indices_from(matrix, k=1)]):.3f}")

    @classmethod
    def _execution_result_similarity(cls, result_a: Dict[str, Any], result_b: Dict[str, Any]) -> float:
        """
        Compare two execution results and return a similarity score.
        """
        # Get common step IDs
        steps_a = set(result_a.keys())
        steps_b = set(result_b.keys())
        
        # Penalize missing/extra steps
        all_steps = steps_a | steps_b
        common_steps = steps_a & steps_b
        
        if not all_steps:
            return 1.0  # Both empty
        
        step_coverage = len(common_steps) / len(all_steps)
        
        # Compare outputs for common steps
        if not common_steps:
            return 0.0
        
        step_similarities = []
        for step_id in common_steps:
            output_a = result_a[step_id]
            output_b = result_b[step_id]
            sim = cls._compare_step_outputs(output_a, output_b)
            step_similarities.append(sim)
        
        avg_step_similarity = np.mean(step_similarities)
        
        # Weighted combination: 70% output similarity, 30% step coverage
        total_score = 0.7 * avg_step_similarity + 0.3 * step_coverage
        
        return total_score

    @classmethod
    def _compare_step_outputs(cls, output_a: Any, output_b: Any) -> float:
        """
        Compare two step outputs and return a similarity score.
        Handles dicts, lists, and primitive types.
        """
        # Handle None cases
        if output_a is None and output_b is None:
            return 1.0
        if output_a is None or output_b is None:
            return 0.0
        
        # Handle dict outputs (most tool outputs)
        if isinstance(output_a, dict) and isinstance(output_b, dict):
            return cls._compare_dicts(output_a, output_b)
        
        # Handle list outputs (LLM results, parameter lists)
        if isinstance(output_a, list) and isinstance(output_b, list):
            return cls._compare_lists(output_a, output_b)
        
        # Handle primitive types
        if type(output_a) == type(output_b):
            if isinstance(output_a, (int, float)):
                # For numeric values, use relative difference
                if output_a == output_b:
                    return 1.0
                max_val = max(abs(output_a), abs(output_b))
                if max_val == 0:
                    return 1.0
                return 1.0 - min(abs(output_a - output_b) / max_val, 1.0)
            elif isinstance(output_a, str):
                return cls._compare_strings(output_a, output_b)
            elif isinstance(output_a, bool):
                return 1.0 if output_a == output_b else 0.0
        
        # Different types or unsupported types
        return 0.0

    @classmethod
    def _compare_dicts(cls, dict_a: Dict, dict_b: Dict) -> float:
        """Compare two dictionaries."""
        keys_a = set(dict_a.keys())
        keys_b = set(dict_b.keys())
        
        all_keys = keys_a | keys_b
        common_keys = keys_a & keys_b
        
        if not all_keys:
            return 1.0
        
        # Key coverage score
        key_coverage = len(common_keys) / len(all_keys)
        
        # Value similarity for common keys
        if not common_keys:
            return 0.0
        
        value_similarities = []
        for key in common_keys:
            sim = cls._compare_step_outputs(dict_a[key], dict_b[key])
            value_similarities.append(sim)
        
        avg_value_similarity = np.mean(value_similarities)
        
        # Weighted: 60% value similarity, 40% key coverage
        return 0.6 * avg_value_similarity + 0.4 * key_coverage

    @classmethod
    def _compare_lists(cls, list_a: List, list_b: List) -> float:
        """Compare two lists."""
        if not list_a and not list_b:
            return 1.0
        if not list_a or not list_b:
            return 0.0
        
        # For lists of dicts (like parameter lists)
        if all(isinstance(x, dict) for x in list_a + list_b):
            return cls._compare_list_of_dicts(list_a, list_b)
        
        # For lists of primitives
        if len(list_a) != len(list_b):
            # Penalize length difference
            len_penalty = min(len(list_a), len(list_b)) / max(len(list_a), len(list_b))
            
            # Compare common elements
            min_len = min(len(list_a), len(list_b))
            if min_len == 0:
                return 0.0
            
            element_similarities = []
            for i in range(min_len):
                sim = cls._compare_step_outputs(list_a[i], list_b[i])
                element_similarities.append(sim)
            
            avg_similarity = np.mean(element_similarities)
            return 0.7 * avg_similarity + 0.3 * len_penalty
        
        # Same length - compare element by element
        element_similarities = []
        for a, b in zip(list_a, list_b):
            sim = cls._compare_step_outputs(a, b)
            element_similarities.append(sim)
        
        return np.mean(element_similarities)

    @classmethod
    def _compare_list_of_dicts(cls, list_a: List[Dict], list_b: List[Dict]) -> float:
        """
        Compare lists of dictionaries (like parameter lists).
        Uses key-based matching for better comparison.
        """
        if not list_a and not list_b:
            return 1.0
        if not list_a or not list_b:
            return 0.0
        
        # Try to match by 'key' field if it exists (for parameter objects)
        keys_a = {d.get('key'): d for d in list_a if 'key' in d}
        keys_b = {d.get('key'): d for d in list_b if 'key' in d}
        
        if keys_a and keys_b:
            # Match by key
            common_keys = set(keys_a.keys()) & set(keys_b.keys())
            all_keys = set(keys_a.keys()) | set(keys_b.keys())
            
            if not all_keys:
                return cls._compare_lists(list_a, list_b)
            
            key_coverage = len(common_keys) / len(all_keys)
            
            if not common_keys:
                return 0.0
            
            value_similarities = []
            for key in common_keys:
                sim = cls._compare_dicts(keys_a[key], keys_b[key])
                value_similarities.append(sim)
            
            avg_similarity = np.mean(value_similarities)
            return 0.7 * avg_similarity + 0.3 * key_coverage
        
        # Fall back to position-based comparison
        return cls._compare_lists(list_a, list_b)

    @classmethod
    def _compare_strings(cls, str_a: str, str_b: str) -> float:
        """
        Compare two strings using multiple methods.
        """
        if str_a == str_b:
            return 1.0
        
        # Normalize strings
        str_a_norm = str_a.strip().lower()
        str_b_norm = str_b.strip().lower()
        
        if str_a_norm == str_b_norm:
            return 0.95
        
        # Jaccard similarity on words
        words_a = set(str_a_norm.split())
        words_b = set(str_b_norm.split())
        
        if not words_a and not words_b:
            return 1.0
        if not words_a or not words_b:
            return 0.0
        
        jaccard = len(words_a & words_b) / len(words_a | words_b)
        
        # Longest common subsequence ratio
        lcs_ratio = cls._lcs_similarity(str_a_norm, str_b_norm)
        
        # Combine metrics
        return 0.6 * jaccard + 0.4 * lcs_ratio

    @classmethod
    def _lcs_similarity(cls, str_a: str, str_b: str) -> float:
        """
        Compute similarity based on longest common subsequence.
        """
        if not str_a or not str_b:
            return 0.0
        
        m, n = len(str_a), len(str_b)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if str_a[i - 1] == str_b[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
        
        lcs_length = dp[m][n]
        return 2.0 * lcs_length / (m + n)
