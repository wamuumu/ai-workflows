import os
import json
import numpy as np
import logging
import torch

from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from collections import Counter
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from utils.logger import LoggerUtils

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) 
LOG_DIR = os.path.join(ROOT, "metrics")

class MetricSet(BaseModel):
    time_taken: float = 0
    number_of_calls: int = 0 
    total_tokens: int = 0 # input + output tokens

class MetricSchema(BaseModel):
    generation: MetricSet = Field(default_factory=MetricSet)
    features: Dict[str, MetricSet] = Field(default_factory=dict)
    execution: MetricSet = Field(default_factory=MetricSet)

class MetricUtils:
    
    _metrics: MetricSchema = MetricSchema()
    _has_finished: bool = False
    _logger = LoggerUtils(name="MetricLogger", log_dir=LOG_DIR, log_to_console=True)
    _embeddings: Dict[str, np.ndarray] = {}
    _similarities: Dict[Tuple, float] = {}
    _embedding_model: SentenceTransformer = None
    

    # ============================ Evaluation Metrics ============================ #

    # ============================================================================ #
    # Utils functions
    # ============================================================================ #

    @classmethod
    def _init_model(cls):
        if not cls._embedding_model:
            gpu_available = torch.cuda.is_available()
            if gpu_available:
                cls._embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cuda')
            else:
                cls._embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
    
    @classmethod
    def _print_similarity_matrix(cls, matrix: np.ndarray, title: str):
        n = matrix.shape[0]
        cls._logger.log(logging.INFO, title)
        header = "    " + "".join([f"W{i+1} ".ljust(6) for i in range(n)])
        cls._logger.log(logging.INFO, header)
        for i in range(n):
            row = f"W{i+1} " + "".join([f"{matrix[i,j]:.2f} ".ljust(6) for j in range(n)])
            cls._logger.log(logging.INFO, row)
    
    @classmethod
    def _string_embedding_score(cls, a: str, b: str) -> float:

        if a == b:
            return 1.0

        # Check if similarity was already computed
        if (a, b) in cls._similarities:
            return cls._similarities[(a, b)]
        if (b, a) in cls._similarities:
            return cls._similarities[(b, a)]

        # Initialize model if needed
        cls._init_model()

        # Encode strings if not cached
        if a not in cls._embeddings:
            emb_a = cls._embedding_model.encode(a, convert_to_numpy=True, normalize_embeddings=True)
            cls._embeddings[a] = emb_a.reshape(1, -1)  # shape (1, dim)

        if b not in cls._embeddings:
            emb_b = cls._embedding_model.encode(b, convert_to_numpy=True, normalize_embeddings=True)
            cls._embeddings[b] = emb_b.reshape(1, -1)  # shape (1, dim)

        # Compute cosine similarity
        score = float(cosine_similarity(cls._embeddings[a], cls._embeddings[b])[0, 0])
        score = max(0.0, min(1.0, score))  # clamp to [0,1]

        # Cache results both ways
        cls._similarities[(a, b)] = score
        cls._similarities[(b, a)] = score

        return score
    
    # ============================================================================ #
    # 1. Similarity Scores
    # For consistency and reproducibility evaluations
    # ============================================================================ #

    @classmethod
    def similarity_scores(cls, workflows: List[BaseModel]) -> None:
        """
        Compute pairwise similarity matrix between multiple workflows.
        """
        n = len(workflows)
        matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(i, n):
                total_score = cls._workflow_similarity(workflows[i], workflows[j])
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
    def _workflow_similarity(cls, a: BaseModel, b: BaseModel) -> float:
        # Align steps
        _, _, _, step_score = cls._align_steps(a.steps, b.steps)

        # Compare transitions
        transition_score = cls._compare_transitions(a.steps, b.steps)

        # Weighted: 70% steps, 30% transitions
        return 0.7 * step_score + 0.3 * transition_score

    @classmethod
    def _align_steps(cls, steps_a: List[BaseModel], steps_b: List[BaseModel]) -> Tuple:
        """
        Align steps using greedy matching based on step similarity.
        Returns matches, unmatched_a, unmatched_b, average_score
        """
        used_b = set()
        matches = []
        total_score = 0.0

        for step_a in steps_a:
            best_score = 0.0
            best_b_idx = None
            for j, step_b in enumerate(steps_b):
                if j in used_b:
                    continue
                s = cls._step_similarity(step_a, step_b)
                if s > best_score:
                    best_score = s
                    best_b_idx = j
            if best_b_idx is not None:
                used_b.add(best_b_idx)
                matches.append((step_a.id, steps_b[best_b_idx].id))
                total_score += best_score

        unmatched_a = [s.id for s in steps_a if s.id not in [m[0] for m in matches]]
        unmatched_b = [s.id for i, s in enumerate(steps_b) if i not in used_b]
        avg_score = total_score / max(len(steps_a), len(steps_b)) if steps_a or steps_b else 0.0
        return matches, unmatched_a, unmatched_b, avg_score

    @classmethod
    def _step_similarity(cls, a: BaseModel, b: BaseModel) -> float:
        # Final steps match only with final
        if hasattr(a, 'is_final') or hasattr(b, 'is_final'):
            return 1.0 if (hasattr(a, 'is_final') and a.is_final) and (hasattr(b, 'is_final') and b.is_final) else 0.0

        # Action must match
        if a.action != b.action:
            return 0.0

        score = 0.0
        weight = 0.0

        # Compare ToolSteps
        if a.action == "call_tool":
            score += 1.0 if a.tool_name == b.tool_name else 0.0
            weight += 1.0

            keys_a = {p.key for p in a.parameters}
            keys_b = {p.key for p in b.parameters}
            if keys_a or keys_b:
                score += len(keys_a & keys_b) / len(keys_a | keys_b)
                weight += 1.0

        # Compare LLMSteps
        if a.action == "call_llm":
            sim = cls._string_embedding_score(a.prompt, b.prompt)
            score += sim
            weight += 1.0

        return score / weight if weight else 0.0

    @classmethod
    def _compare_transitions(cls, steps_a: List[BaseModel], steps_b: List[BaseModel]) -> float:
        """
        Compare transition edges, including conditions.
        """
        edges_a = cls._extract_transitions(steps_a)
        edges_b = cls._extract_transitions(steps_b)
        
        if not edges_a and not edges_b:
            return 1.0
        if not edges_a or not edges_b:
            return 0.0

        total = 0.0
        for e_a in edges_a:
            best_sim = 0.0
            for e_b in edges_b:
                from_sim = 1.0 if e_a[0] == e_b[0] else 0.0
                to_sim = 1.0 if e_a[1] == e_b[1] else 0.0
                cond_sim = cls._string_embedding_score(e_a[2], e_b[2])
                sim = 0.4 * from_sim + 0.4 * to_sim + 0.2 * cond_sim
                if sim > best_sim:
                    best_sim = sim
            total += best_sim
        return total / max(len(edges_a), len(edges_b))

    @classmethod
    def _extract_transitions(cls, steps: List[BaseModel]) -> List[Tuple[str, str, str]]:
        """
        Return list of (from_step_id, to_step_id, condition) for comparison.
        """
        edges = []
        for step in steps:
            transitions = getattr(step, "transitions", [])
            for t in transitions or []:
                edges.append((step.id, t.next_step, t.condition))
        return edges
    
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

        results = []
        for idx, workflow in enumerate(workflows):
            # Expected tool calls
            tool_count = Counter(step.tool_name for step in workflow.steps if not hasattr(step, "is_final") and step.action == "call_tool")
            expected_tool_calls = reference_data.get("expected_tool_calls", {})
        
            tool_scores = []
            for tool, limits in expected_tool_calls.items(): 
                count = tool_count.get(tool, 0)
                min_calls, max_calls = limits.get("min", 0), limits.get("max", float('inf'))
                tool_scores.append(cls._get_score(count, min_calls, max_calls))

            # Expected LLM calls
            llm_count = sum(1 for step in workflow.steps if not hasattr(step, "is_final") and step.action == "call_llm")
            expected_llm_calls = reference_data.get("expected_llm_calls", {})
            if expected_llm_calls and len(expected_llm_calls) == 2:
                min_calls, max_calls = expected_llm_calls.get("min", 0), expected_llm_calls.get("max", float('inf'))
                llm_score = cls._get_score(llm_count, min_calls, max_calls)
            else:
                llm_score = 0.0

            # Expected total steps
            total_steps = sum(1 for step in workflow.steps if not hasattr(step, "is_final"))
            expected_total_steps = reference_data.get("expected_step_count_range", [])
            if expected_total_steps and len(expected_total_steps) == 2:
                min_steps, max_steps = expected_total_steps.get("min", 0), expected_total_steps.get("max", float('inf'))
                step_score = cls._get_score(total_steps, min_steps, max_steps)
            else:
                step_score = 0.0

            # Expected branch transitions
            transition_score = 0
            branching_nodes = [step for step in workflow.steps if hasattr(step, "transitions") and step.action == "call_llm" and len(step.transitions) > 1]
            if branching_nodes:
                expected_branching = reference_data.get("expected_branch_transitions", {})
                for _, constraints in expected_branching.items():
                    keywords = constraints.get("keywords", [])
                    for step in branching_nodes:
                        if any(kw in step.prompt for kw in keywords):
                            branch_count = len(step.transitions)
                            if constraints.get("transitions", 0) == branch_count:
                                transition_score += 1
            
                transition_score = transition_score / max(len(branching_nodes), 1)
            
            reference_goal = reference_data.get("expected_goal", "")
            goal_score = cls._string_embedding_score(workflow.target_objective, reference_goal)
            
            reference_thoughts = "\n".join(reference_data.get("expected_thoughts", []))
            workflow_thoughts = "\n".join(step.thoughts for step in workflow.steps if not hasattr(step, "is_final"))
            thoughts_score = cls._string_embedding_score(workflow_thoughts, reference_thoughts)

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
        temp_texts = ["","","","","","",""]
        cls._logger.log(logging.INFO, f"    Formatted data:")
        for result in results:
            temp_texts[0]+=(f"{np.mean(result['tool_scores']):.3f}, ")
            temp_texts[1]+=(f"{result['llm_score']:.3f}, ")
            temp_texts[2]+=(f"{result['step_score']:.3f}, ")
            temp_texts[3]+=(f"{result['transition_score']:.3f}, ")
            temp_texts[4]+=(f"{result['overall_weighted_score']:.3f}, ")
            temp_texts[5]+=(f"{result['goal_score']:.3f}, ")
            temp_texts[6]+=(f"{result['thoughts_score']:.3f}, ")
        for line in temp_texts:
            cls._logger.log(logging.INFO, "" + "".join(line)[:-2])
        
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
    
    # ============================================================================ #
    # 3. Execution Result Similarity Scores
    # For comparing actual execution outputs across multiple runs
    # ============================================================================ #

    @classmethod
    def execution_similarity_scores(cls, execution_results: List[Dict[str, Any]]) -> None:
        """
        Compute and print pairwise similarity matrix between execution results.
        
        Args:
            execution_results: List of execution result dictionaries,
                            each mapping step_id -> step_output
        """
        n = len(execution_results)
        matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(i, n):
                score = cls._execution_result_similarity(
                    execution_results[i],
                    execution_results[j]
                )
                matrix[i, j] = score
                matrix[j, i] = score

        # Print matrix (reuse your existing utility)
        cls._print_similarity_matrix(
            matrix,
            title="Execution Result Similarity Matrix"
        )

        # Aggregate statistics (upper triangle, excluding diagonal)
        triu = matrix[np.triu_indices_from(matrix, k=1)]
        if triu.size > 0:
            avg_similarity = float(np.mean(triu))
            std_similarity = float(np.std(triu))
            min_similarity = float(np.min(triu))
            max_similarity = float(np.max(triu))
        else:
            avg_similarity = std_similarity = min_similarity = max_similarity = 1.0

        cls._logger.log(logging.INFO, f"Average pairwise similarity: {avg_similarity:.3f}")
        cls._logger.log(logging.INFO, f"Standard deviation: {std_similarity:.3f}")
        cls._logger.log(logging.INFO, f"Min similarity: {min_similarity:.3f}")
        cls._logger.log(logging.INFO, f"Max similarity: {max_similarity:.3f}\n")

    @classmethod
    def _compare_step_outputs(cls, output_a: Any, output_b: Any) -> float:
        if output_a is None and output_b is None:
            return 1.0
        if output_a is None or output_b is None:
            return 0.0

        # Dict vs dict
        if isinstance(output_a, dict) and isinstance(output_b, dict):
            return cls._compare_dicts(output_a, output_b)

        # List vs list
        if isinstance(output_a, list) and isinstance(output_b, list):
            return cls._compare_lists(output_a, output_b)

        # Same primitive types
        if type(output_a) == type(output_b):
            if isinstance(output_a, (int, float)):
                if output_a == output_b:
                    return 1.0
                max_val = max(abs(output_a), abs(output_b))
                if max_val == 0:
                    return 1.0
                return 1.0 - min(abs(output_a - output_b) / max_val, 1.0)
            if isinstance(output_a, str):
                return cls._string_embedding_score(output_a, output_b)
            if isinstance(output_a, bool):
                return 1.0 if output_a == output_b else 0.0

        # Different types or unsupported types
        return 0.0

    @classmethod
    def _compare_dicts(cls, dict_a: Dict, dict_b: Dict) -> float:
        keys_a, keys_b = set(dict_a.keys()), set(dict_b.keys())
        all_keys = keys_a | keys_b
        if not all_keys:
            return 1.0
        common_keys = keys_a & keys_b
        key_coverage = len(common_keys) / len(all_keys)
        if not common_keys:
            return 0.0
        sims = [cls._compare_step_outputs(dict_a[k], dict_b[k]) for k in common_keys]
        avg_val_sim = float(np.mean(sims)) if sims else 0.0
        # Weighted blend: value similarity + key coverage
        return 0.6 * avg_val_sim + 0.4 * key_coverage

    @classmethod
    def _compare_list_of_dicts(cls, list_a: List[Dict], list_b: List[Dict]) -> float:
        if not list_a and not list_b:
            return 1.0
        if not list_a or not list_b:
            return 0.0
        keys_a = {d.get('key'): d for d in list_a if 'key' in d}
        keys_b = {d.get('key'): d for d in list_b if 'key' in d}
        # If 'key' fields available, match by key
        if keys_a and keys_b:
            all_keys = set(keys_a.keys()) | set(keys_b.keys())
            if not all_keys:
                return cls._compare_lists(list_a, list_b)
            common = set(keys_a.keys()) & set(keys_b.keys())
            if not common:
                return 0.0
            sims = [cls._compare_dicts(keys_a[k], keys_b[k]) for k in common]
            avg_sim = float(np.mean(sims))
            key_coverage = len(common) / len(all_keys)
            return 0.7 * avg_sim + 0.3 * key_coverage
        # Fallback to lists comparison
        return cls._compare_lists(list_a, list_b)

    @classmethod
    def _compare_lists(cls, list_a: List, list_b: List) -> float:
        if not list_a and not list_b:
            return 1.0
        if not list_a or not list_b:
            return 0.0
        # If lists are lists of dicts -> specialized comparator
        if all(isinstance(x, dict) for x in list_a + list_b):
            return cls._compare_list_of_dicts(list_a, list_b)
        # If lists of primitives -> treat as multisets (order-insensitive)
        if all(not isinstance(x, (list, dict)) for x in list_a + list_b):
            used_b = [False] * len(list_b)
            sims = []
            for a in list_a:
                best_sim, best_j = -1.0, -1
                for j, b in enumerate(list_b):
                    if used_b[j]:
                        continue
                    s = cls._compare_step_outputs(a, b)
                    if s > best_sim:
                        best_sim, best_j = s, j
                if best_j >= 0:
                    used_b[best_j] = True
                    sims.append(best_sim)
            if not sims:
                return 0.0
            len_penalty = min(len(list_a), len(list_b)) / max(len(list_a), len(list_b))
            return 0.7 * float(np.mean(sims)) + 0.3 * len_penalty
        # Fallback positional comparison
        min_len = min(len(list_a), len(list_b))
        sims = [cls._compare_step_outputs(list_a[i], list_b[i]) for i in range(min_len)]
        if not sims:
            return 0.0
        len_penalty = min_len / max(len(list_a), len(list_b))
        return 0.7 * float(np.mean(sims)) + 0.3 * len_penalty

    @classmethod
    def _execution_result_similarity(cls, result_a: Dict[str, Any], result_b: Dict[str, Any],
                                    weight_output: float = 0.7, weight_coverage: float = 0.3
                                ) -> float:
        """
        Compare two execution results with step alignment (handles renumbered steps).
        Returns a score in [0,1].
        """
        steps_a = list(result_a.keys())
        steps_b = list(result_b.keys())
        nA, nB = len(steps_a), len(steps_b)
        if nA == 0 and nB == 0:
            return 1.0
        if nA == 0 or nB == 0:
            return 0.0

        # Build pairwise similarity matrix between step outputs
        sim_mat = np.zeros((nA, nB))
        for i, a in enumerate(steps_a):
            for j, b in enumerate(steps_b):
                sim_mat[i, j] = cls._compare_step_outputs(result_a[a], result_b[b])

        # Greedy max-weight matching (fast and deterministic)
        matched_a = set()
        matched_b = set()
        matched_sims = []
        while True:
            # find global max
            i, j = divmod(int(sim_mat.argmax()), sim_mat.shape[1])
            maxv = sim_mat[i, j]
            if maxv <= 0:
                break
            if i in matched_a or j in matched_b:
                sim_mat[i, j] = -1.0
                continue
            matched_a.add(i); matched_b.add(j)
            matched_sims.append(maxv)
            # block row and column
            sim_mat[i, :] = -1.0
            sim_mat[:, j] = -1.0

        matched_count = len(matched_sims)
        total_steps = max(nA, nB)
        coverage = matched_count / total_steps if total_steps > 0 else 1.0
        avg_output_sim = float(np.mean(matched_sims)) if matched_sims else 0.0
        return weight_output * avg_output_sim + weight_coverage * coverage

    # ============================================================================ #
    # 4. Efficiency Metrics
    # For tracking time, number of calls and token usage
    # ============================================================================ #

    @classmethod
    def update(cls, category: str, start_time: float, end_time: float, tokens: int) -> None:

        fields = MetricSchema.model_fields

        if category not in fields:
            metric_set: Dict[str, MetricSet] = getattr(cls._metrics, "features")
            if category not in metric_set:
                metric_set[category] = MetricSet()
            metric_set = metric_set[category]
        else:
            metric_set: MetricSet = getattr(cls._metrics, category)
        
        metric_set.time_taken += end_time - start_time
        metric_set.number_of_calls += 1
        metric_set.total_tokens += tokens
    
    @classmethod
    def finish(cls) -> None:
        cls._has_finished = True

    @classmethod
    def display(cls) -> List[str]:
        def print_metric_set(title: str, metric_set: MetricSet, indent: int = 0):
            prefix = " " * indent
            cls._logger.log(logging.INFO, f"{prefix}{title}:")
            cls._logger.log(logging.INFO, f"{prefix}  time_taken       : {metric_set.time_taken:.4f}s")
            cls._logger.log(logging.INFO, f"{prefix}  number_of_calls  : {metric_set.number_of_calls}")
            cls._logger.log(logging.INFO, f"{prefix}  total_tokens     : {metric_set.total_tokens}")
        
        def get_formatted_metric_set(metric_set: MetricSet) -> List[str]:
            line = f"{metric_set.time_taken:.2f}, {metric_set.number_of_calls}, {metric_set.total_tokens}"
            return line

        # Generation metrics
        print_metric_set("Generation", cls._metrics.generation)

        # Execution metrics
        print_metric_set("Execution", cls._metrics.execution)

        # Feature-level metrics
        if cls._metrics.features:
            cls._logger.log(logging.INFO, "Features:")
            for feature_name, feature_metrics in cls._metrics.features.items():
                print_metric_set(feature_name, feature_metrics, indent=2)
        else:
            cls._logger.log(logging.INFO, "Features: None")
        
        return [
            get_formatted_metric_set(cls._metrics.generation),
            get_formatted_metric_set(cls._metrics.execution)
        ]

    @classmethod
    def display_formatted_metrics(cls, metrics: List[List[str]]) -> None:
        headers = ["Generation", "Execution"]
        for header, column in zip(headers, zip(*metrics)):
            cls._logger.log(logging.INFO, f"Formatted {header} Metrics:")
            for value in column:
                cls._logger.log(logging.INFO, f"  {value}")
            
    @classmethod
    def reset(cls) -> None:
        """Reset metrics for a new run."""
        cls._metrics = MetricSchema()
