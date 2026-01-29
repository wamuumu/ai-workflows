import os
import re
import json
import numpy as np
import logging

from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from collections import Counter
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from tools.registry import ToolRegistry
from utils.logger import LoggerUtils

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) 
LOG_DIR = os.path.join(ROOT, "metrics")
BERT_DIR = os.path.join(ROOT, "models")

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
    _formatted_logger = LoggerUtils(name="FormattedMetricLogger", log_dir=LOG_DIR, prefix="formatted")
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
            if not os.path.exists(BERT_DIR):
                os.makedirs(BERT_DIR, exist_ok=True)
            model_path = os.path.join(BERT_DIR, 'all-MiniLM-L6-v2')
            if not os.path.exists(model_path):
                cls._logger.log(logging.INFO, "Downloading embedding model...")
                cls._embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device="cpu")
                cls._logger.log(logging.INFO, f"Saving embedding model to: {model_path}...")
                cls._embedding_model.save(os.path.join(BERT_DIR, 'all-MiniLM-L6-v2'))
            else:
                cls._logger.log(logging.INFO, f"Loading embedding model: {model_path}...")
                cls._embedding_model = SentenceTransformer(model_path, device="cpu")
    
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

        formatted_txt = ""
        for i in range(n):
            for j in range(i, n):
                total_score = cls._workflow_similarity(workflows[i], workflows[j])
                matrix[i, j] = total_score
                matrix[j, i] = total_score  # symmetric
        
        for line in matrix:
            formatted_txt += "".join([f"{score:.3f}, " for score in line])[:-2] + "\n"

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

        cls._formatted_logger.log(logging.INFO, f"    Formatted data similarity scores:")
        cls._formatted_logger.log(logging.INFO, "\n" + formatted_txt)

    @classmethod
    def _workflow_similarity(cls, a: BaseModel, b: BaseModel) -> float:
        # Align steps and get the mapping
        matches, _, _, step_score = cls._align_steps(a.steps, b.steps)
        
        # Build ID mapping from alignment: a_id -> b_id
        id_mapping = {m[0]: m[1] for m in matches}

        # Compare transitions using alignment
        transition_score = cls._compare_transitions(a.steps, b.steps, id_mapping)

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
        # Check if steps are FinalSteps (check value, not just attribute existence)
        a_is_final = getattr(a, 'is_final', False) == True
        b_is_final = getattr(b, 'is_final', False) == True
        
        # Final steps match only with final
        if a_is_final or b_is_final:
            return 1.0 if a_is_final and b_is_final else 0.0

        # Non-final steps must have action attribute
        if not hasattr(a, 'action') or not hasattr(b, 'action'):
            return 0.0

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
    def _compare_transitions(cls, steps_a: List[BaseModel], steps_b: List[BaseModel], 
                            id_mapping: Dict[int, int] = None) -> float:
        """
        Compare transition edges, including conditions.
        Uses id_mapping to compare aligned steps rather than raw IDs.
        
        Args:
            steps_a: Steps from workflow A
            steps_b: Steps from workflow B  
            id_mapping: Mapping from step IDs in A to aligned step IDs in B
        """
        edges_a = cls._extract_transitions(steps_a)
        edges_b = cls._extract_transitions(steps_b)
        
        if not edges_a and not edges_b:
            return 1.0
        if not edges_a or not edges_b:
            return 0.0
        
        if id_mapping is None:
            id_mapping = {}

        total = 0.0
        for e_a in edges_a:
            best_sim = 0.0
            for e_b in edges_b:
                # Use alignment mapping: check if e_a's from/to map to e_b's from/to
                from_a, to_a, cond_a = e_a
                from_b, to_b, cond_b = e_b
                
                # Check if 'from' steps are aligned
                from_sim = 1.0 if id_mapping.get(from_a) == from_b else 0.0
                # Check if 'to' steps are aligned  
                to_sim = 1.0 if id_mapping.get(to_a) == to_b else 0.0
                # Compare conditions semantically
                cond_sim = cls._string_embedding_score(cond_a, cond_b)
                
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
            # Expected tool calls (properly check for action attribute, not is_final existence)
            tool_count = Counter(
                step.tool_name for step in workflow.steps 
                if hasattr(step, 'action') and step.action == "call_tool"
            )

            tool_scores = []
            expected_tool_calls = reference_data.get("expected_tool_calls", {})
            if expected_tool_calls: 
                for category in expected_tool_calls:
                    category_scores = []
                    for tool, limits in expected_tool_calls[category].items():
                        count = tool_count.get(tool, 0)
                        min_calls, max_calls = limits.get("min", 0), limits.get("max", float('inf'))
                        category_scores.append(max(0, cls._get_score(count, min_calls, max_calls)))
                    tool_scores.append(max(category_scores) if category_scores else 0.0)
            
            llm_count = sum(1 for step in workflow.steps if hasattr(step, 'action') and step.action == "call_llm")
            expected_llm_calls = reference_data.get("expected_llm_calls", {})
            if expected_llm_calls:
                min_calls, max_calls = expected_llm_calls.get("min", 0), expected_llm_calls.get("max", float('inf'))
                llm_score = max(0, cls._get_score(llm_count, min_calls, max_calls))
            
            total_steps = sum(1 for step in workflow.steps if not getattr(step, 'is_final', False))
            expected_total_steps = reference_data.get("expected_step_count_range", {})
            if expected_total_steps:
                min_steps, max_steps = expected_total_steps.get("min", 0), expected_total_steps.get("max", float('inf'))
                step_score = max(0, cls._get_score(total_steps, min_steps, max_steps))

            expected_branching = reference_data.get("expected_branch_transitions", {})
            branching_steps = cls._get_branching_steps(workflow)
            if expected_branching:
                matched = 0
                for _, constraint in expected_branching.items():
                    if any(cls._matches_branch_constraint(step, constraint) for step in branching_steps):
                        matched += 1
                transition_score = matched / max(len(expected_branching), 1)  

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
                    "transition_score": transition_score
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
        temp_texts = ["","","","",""]
        cls._formatted_logger.log(logging.INFO, f"    Formatted data correctness scores:")
        for result in results:
            temp_texts[0]+=(f"{np.mean(result['tool_scores']):.3f}, ")
            temp_texts[1]+=(f"{result['llm_score']:.3f}, ")
            temp_texts[2]+=(f"{result['step_score']:.3f}, ")
            temp_texts[3]+=(f"{result['transition_score']:.3f}, ")
            temp_texts[4]+=(f"{result['overall_weighted_score']:.3f}, ")
        
        temp_text=""
        for line in temp_texts:
            temp_text+=("  "+ "".join(line)[:-2] + "\n")    
        cls._formatted_logger.log(logging.INFO, "\n"+temp_text)
        
        # cls._logger.log aggregate statistics
        overall_scores = [r['overall_score'] for r in results]
        cls._logger.log(logging.INFO, f"  Average correctness score: {np.mean(overall_scores):.3f}")
        cls._logger.log(logging.INFO, f"  Min correctness score: {np.min(overall_scores):.3f}")
        cls._logger.log(logging.INFO, f"  Max correctness score: {np.max(overall_scores):.3f}")
    
    @classmethod
    def _get_branching_steps(cls, workflow: BaseModel) -> List[dict]:
        return [
            {
                "prompt": step.prompt.lower(),
                "thoughts": (getattr(step, "thoughts", "") or "").lower(),
                "transition_count": len(step.transitions),
                "conditions": [t.condition.lower() for t in step.transitions],
            }
            for step in workflow.steps
            if hasattr(step, 'action')
            and step.action == "call_llm"
            and hasattr(step, "transitions")
            and len(step.transitions) > 1
        ]
    
    @classmethod
    def _matches_branch_constraint(cls, step, constraint):
        keywords = [kw.lower() for kw in constraint.get("keywords", [])]
        expected_transitions = constraint.get("transitions", 0)

        # 1. Intent match (prompt OR thoughts)
        intent_match = any(
            kw in step.get("prompt", "") or kw in step.get("thoughts", "")
            for kw in keywords
        )

        if not intent_match:
            return False

        # 2. Structural match
        if step.get("transition_count", 0) != expected_transitions:
            return False

        return True

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

        formatted_txt = ""
        for i in range(n):
            for j in range(i, n):
                score = cls._execution_result_similarity(
                    execution_results[i],
                    execution_results[j]
                )
                matrix[i, j] = score
                matrix[j, i] = score
        
        for line in matrix:
            formatted_txt += "".join([f"{score:.3f}, " for score in line])[:-2] + "\n"

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

        cls._formatted_logger.log(logging.INFO, f"    Formatted data similarity scores:")
        cls._formatted_logger.log(logging.INFO, "\n" + formatted_txt)

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
        
        # Different keys or no 'key' field -> fallback to positional
        return 0.0
    
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
    def display(cls) -> Dict[str, str]:
        def print_metric_set(title: str, metric_set: MetricSet, indent: int = 0):
            prefix = " " * indent
            cls._logger.log(logging.INFO, f"{prefix}{title}:")
            cls._logger.log(logging.INFO, f"{prefix}  time_taken       : {metric_set.time_taken:.4f}s")
            cls._logger.log(logging.INFO, f"{prefix}  number_of_calls  : {metric_set.number_of_calls}")
            cls._logger.log(logging.INFO, f"{prefix}  total_tokens     : {metric_set.total_tokens}")
        
        def get_formatted_metric_set(metric_set: MetricSet) -> str:
            line = f"{metric_set.time_taken:.2f}, {metric_set.number_of_calls}, {metric_set.total_tokens}"
            return line

        # Generation metrics
        print_metric_set("Generation", cls._metrics.generation)

        # Execution metrics
        print_metric_set("Execution", cls._metrics.execution)

        formatted_lines = {
            "generation": get_formatted_metric_set(cls._metrics.generation),
            "execution": get_formatted_metric_set(cls._metrics.execution)
        }

        # Feature-level metrics
        if cls._metrics.features:
            cls._logger.log(logging.INFO, "Features:")
            for feature_name, feature_metrics in cls._metrics.features.items():
                print_metric_set(feature_name, feature_metrics, indent=2)
                formatted_lines[feature_name] = get_formatted_metric_set(feature_metrics)
        else:
            cls._logger.log(logging.INFO, "Features: None")
        
        return formatted_lines

    @classmethod
    def display_formatted_metrics(cls, metrics: List[Dict[str, str]]) -> None:    
        
        headers = set()
        for group in metrics:
            for key in group.keys():
                headers.add(key)
        headers = list(headers)
        
        for header in headers:
            cls._formatted_logger.log(logging.INFO, f"Formatted {header} Metrics:")
            for group in metrics:
                if header in group:
                    cls._formatted_logger.log(logging.INFO, f"  {group[header]}")
                else:
                    cls._formatted_logger.log(logging.INFO, f"  N/A")
            
    @classmethod
    def reset(cls) -> None:
        """Reset metrics for a new run."""
        cls._metrics = MetricSchema()
        cls._embeddings.clear()
        cls._similarities.clear()
        cls._has_finished = False

    # ============================================================================ #
    # 5. Reasoning Coherence Score
    # Measures logical structure and consistency of reasoning chain
    # ============================================================================ #

    @classmethod
    def reasoning_coherence_scores(cls, workflows: List[BaseModel]) -> None:

        results = []
        cls._logger.log(logging.INFO, "Reasoning Coherence Scores:")
        for idx, workflow in enumerate(workflows):
            
            steps = [s for s in workflow.steps if not getattr(s, 'is_final', False)]
            
            if len(steps) == 0:
                return {"coherence_score": 0.0, "details": "No non-final steps"}
            
            # 1. Thought chain continuity
            thought_continuity = cls._analyze_thought_continuity(steps)
            
            # 2. Transition validity
            transition_validity = cls._analyze_transition_validity(steps)
            
            # 3. Structural coherence (detect cycles, unreachable steps)
            structural_coherence = cls._analyze_structural_coherence(workflow.steps)
            
            # 4. Action-thought alignment (does the action match what the thought says?)
            action_alignment = cls._analyze_action_thought_alignment(steps)
            
            # Weighted overall score
            weights = {
                "thought_continuity": 0.30,
                "transition_validity": 0.25,
                "structural_coherence": 0.25,
                "action_alignment": 0.20
            }
            
            overall = (
                thought_continuity * weights["thought_continuity"] +
                transition_validity * weights["transition_validity"] +
                structural_coherence * weights["structural_coherence"] +
                action_alignment * weights["action_alignment"]
            )

            results.append(overall)
            
            cls._logger.log(logging.INFO, f"Worflow W{idx + 1}:")
            cls._logger.log(logging.INFO, f"  Overall coherence score: {overall:.3f}")
            cls._logger.log(logging.INFO, f"  Thought continuity: {thought_continuity:.3f}")
            cls._logger.log(logging.INFO, f"  Transition validity: {transition_validity:.3f}")
            cls._logger.log(logging.INFO, f"  Structural coherence: {structural_coherence:.3f}")
            cls._logger.log(logging.INFO, f"  Action-thought alignment: {action_alignment:.3f}\n")
        
        cls._formatted_logger.log(logging.INFO, f"    Formatted data reasoning coherence scores:")
        cls._formatted_logger.log(logging.INFO, "\n" + "".join([f"{r:.3f}, " for r in results])[:-2] + "\n")

    @classmethod
    def _analyze_thought_continuity(cls, steps: List[BaseModel]) -> float:
        """Check if consecutive thoughts logically follow each other."""
        if len(steps) < 2:
            return 1.0
        
        continuity_scores = []
        for i in range(len(steps) - 1):
            thought_a = getattr(steps[i], 'thoughts', '') or ''
            thought_b = getattr(steps[i + 1], 'thoughts', '') or ''
            
            if not thought_a or not thought_b:
                continuity_scores.append(0.5)  # Neutral if thoughts missing
                continue
            
            # Semantic similarity between consecutive thoughts
            sim = cls._string_embedding_score(thought_a, thought_b)
            
            # Also check for logical progression keywords
            progression_bonus = 0.0
            progression_patterns = [
                (r'\b(then|next|after|following|subsequently)\b', 0.1),
                (r'\b(result|output|using|with the)\b', 0.1),
                (r'\b(based on|from the|given the)\b', 0.1),
            ]
            for pattern, bonus in progression_patterns:
                if re.search(pattern, thought_b.lower()):
                    progression_bonus += bonus
            
            score = min(1.0, sim * 0.7 + 0.3 + progression_bonus)
            continuity_scores.append(score)
        
        return float(np.mean(continuity_scores)) if continuity_scores else 1.0

    @classmethod
    def _analyze_transition_validity(cls, steps: List[BaseModel]) -> float:
        """Check if transitions are justified by step capabilities."""
        transition_scores = []
        
        for step in steps:
            transitions = getattr(step, 'transitions', []) or []
            if not transitions:
                continue
            
            step_thought = getattr(step, 'thoughts', '') or ''
            step_action = getattr(step, 'action', '') or ''
            
            for t in transitions:
                condition = getattr(t, 'condition', '') or ''
                
                # Check if condition relates to step content
                condition_relevance = 0.0
                
                # For LLM steps, conditions should relate to the prompt/decision
                if step_action == 'call_llm':
                    prompt = getattr(step, 'prompt', '') or ''
                    condition_relevance = cls._string_embedding_score(condition, prompt)
                
                # For tool steps, conditions should relate to tool output
                elif step_action == 'call_tool':
                    tool_name = getattr(step, 'tool_name', '') or ''
                    tool_output_keys = [out.get("key") for out in ToolRegistry.get(tool_name).outputs]
                    # Basic check: condition mentions tool-related concepts
                    if tool_name.lower() in condition.lower() or any(k and k.lower() in condition.lower() for k in tool_output_keys):
                        condition_relevance = 0.7
                    else:
                        condition_relevance = cls._string_embedding_score(condition, step_thought)
                
                transition_scores.append(max(0.5, condition_relevance))
        
        return float(np.mean(transition_scores)) if transition_scores else 1.0

    @classmethod
    def _analyze_structural_coherence(cls, steps: List[BaseModel]) -> float:
        """Detect structural issues: cycles, unreachable steps, dead ends."""
        if not steps:
            return 0.0
        
        step_ids = {s.id for s in steps}
        final_step_ids = {s.id for s in steps if getattr(s, 'is_final', False)}
        
        # Build adjacency from transitions
        graph = {s.id: [] for s in steps}
        for step in steps:
            transitions = getattr(step, 'transitions', []) or []
            for t in transitions:
                next_id = getattr(t, 'next_step', None)
                if next_id is not None:
                    graph[step.id].append(next_id)
        
        issues = 0
        total_checks = 0
        
        # Check 1: All transition targets exist
        for step_id, targets in graph.items():
            for target in targets:
                total_checks += 1
                if target not in step_ids:
                    issues += 1
        
        # Check 2: Reachability from step 1 (if exists)
        if 1 in step_ids:
            reachable = cls._find_reachable(graph, 1)
            for step_id in step_ids:
                if step_id != 1:
                    total_checks += 1
                    if step_id not in reachable:
                        issues += 0.5  # Unreachable is a partial issue
        
        # Check 3: Dead ends (non-final steps with no transitions)
        for step in steps:
            if getattr(step, 'is_final', False):
                continue
            transitions = getattr(step, 'transitions', []) or []
            total_checks += 1
            if not transitions:
                issues += 0.5  # Dead end is a partial issue
        
        # Check 4: Path to final exists
        if final_step_ids and 1 in step_ids:
            can_reach_final = any(
                fid in cls._find_reachable(graph, 1) 
                for fid in final_step_ids
            )
            total_checks += 1
            if not can_reach_final:
                issues += 1
        
        if total_checks == 0:
            return 1.0
        
        return max(0.0, 1.0 - (issues / total_checks))

    @classmethod
    def _find_reachable(cls, graph: Dict[int, List[int]], start: int) -> set:
        """BFS to find all reachable nodes from start."""
        visited = set()
        queue = [start]
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    queue.append(neighbor)
        return visited

    @classmethod
    def _analyze_action_thought_alignment(cls, steps: List[BaseModel]) -> float:
        """Check if the action matches what the thought describes."""
        alignment_scores = []
        
        for step in steps:
            thought = getattr(step, 'thoughts', '') or ''
            action = getattr(step, 'action', '') or ''
            
            if not thought:
                alignment_scores.append(0.5)
                continue
            
            thought_lower = thought.lower()
            
            if action == 'call_tool':
                tool_name = getattr(step, 'tool_name', '') or ''
                # Check if thought mentions the tool or its purpose
                tool_words = tool_name.replace('_', ' ').lower().split()
                mention_score = sum(1 for w in tool_words if w in thought_lower) / max(len(tool_words), 1)
                
                # Also check for action-related keywords
                action_keywords = ['call', 'use', 'invoke', 'get', 'fetch', 'compute', 'analyze', 'send']
                has_action_word = any(kw in thought_lower for kw in action_keywords)
                
                score = mention_score * 0.6 + (0.4 if has_action_word else 0.2)
                alignment_scores.append(min(1.0, score))
                
            elif action == 'call_llm':
                # Check if thought mentions reasoning/decision/analysis
                llm_keywords = ['decide', 'determine', 'analyze', 'reason', 'evaluate', 'consider', 'check', 'verify']
                has_llm_word = any(kw in thought_lower for kw in llm_keywords)
                alignment_scores.append(0.8 if has_llm_word else 0.5)
            else:
                alignment_scores.append(0.5)
        
        return float(np.mean(alignment_scores)) if alignment_scores else 1.0

    # ============================================================================ #
    # 6. Intent Resolution Score
    # Measures how well agent interprets underlying goal vs literal prompt
    # ============================================================================ #

    @classmethod
    def intent_resolution_scores(cls, workflows: List[BaseModel]) -> None:

        results = []
        cls._logger.log(logging.INFO, "Intent Resolution Scores:")
        for idx, workflow in enumerate(workflows):
            
            prompt = workflow.metadata.original_prompt or ""

            # 1. Goal alignment (explicit)
            goal = getattr(workflow, 'target_objective', '') or ''
            explicit_alignment = cls._string_embedding_score(goal, prompt)
            
            # 2. Over-interpretation penalty (adding things not in prompt)
            over_interpretation = cls._analyze_over_interpretation(prompt, workflow)
            
            # Overall intent resolution
            weights = {
                "explicit_alignment": 0.75,
                "precision": 0.25  # 1 - over_interpretation
            }
            
            overall = (
                explicit_alignment * weights["explicit_alignment"] +
                (1.0 - over_interpretation) * weights["precision"]
            )

            results.append(overall)
            
            cls._logger.log(logging.INFO, f"Worflow W{idx + 1}:")
            cls._logger.log(logging.INFO, f"  Overall intent resolution: {overall:.3f}")
            cls._logger.log(logging.INFO, f"  Explicit goal alignment: {explicit_alignment:.3f}")
            cls._logger.log(logging.INFO, f"  Over-interpretation penalty: {over_interpretation:.3f}\n") 

        cls._formatted_logger.log(logging.INFO, f"    Formatted data intent resolution scores:")
        cls._formatted_logger.log(logging.INFO, "\n"+"".join([f"{r:.3f}, " for r in results])[:-2] + "\n")

    @classmethod
    def _workflow_to_text(cls, workflow: BaseModel) -> str:
        """Convert workflow to text representation for semantic comparison."""
        parts = [
            workflow.title if hasattr(workflow, 'title') else '',
            workflow.description if hasattr(workflow, 'description') else '',
            workflow.target_objective if hasattr(workflow, 'target_objective') else ''
        ]
        
        for step in workflow.steps:
            if getattr(step, 'is_final', False):
                continue
            parts.append(getattr(step, 'thoughts', '') or '')
            if hasattr(step, 'tool_name'):
                parts.append(step.tool_name.replace('_', ' '))
            if hasattr(step, 'prompt'):
                parts.append(step.prompt)
        
        return ' '.join(p for p in parts if p)

    @classmethod
    def _analyze_over_interpretation(cls, prompt: str, workflow: BaseModel) -> float:
        """
        Detect if workflow adds significant content not implied by prompt.
        Returns penalty score (0 = no over-interpretation, 1 = severe).
        """
        workflow_text = cls._workflow_to_text(workflow)
        
        # Check if workflow text diverges significantly from prompt
        base_similarity = cls._string_embedding_score(prompt, workflow_text)
        
        # Count tools/steps that don't seem related to prompt
        unrelated_steps = 0
        total_steps = 0
        
        for step in workflow.steps:
            if getattr(step, 'is_final', False):
                continue
            total_steps += 1
            
            step_text = getattr(step, 'thoughts', '') or ''
            if hasattr(step, 'tool_name'):
                step_text += ' ' + step.tool_name.replace('_', ' ')
            
            if step_text:
                step_relevance = cls._string_embedding_score(step_text, prompt)
                if step_relevance < 0.3:  # Low relevance threshold
                    unrelated_steps += 1
        
        if total_steps == 0:
            return 0.0
        
        unrelated_ratio = unrelated_steps / total_steps
        
        # Combine with overall divergence
        divergence = 1.0 - base_similarity
        
        # Over-interpretation is high divergence + unrelated steps
        return min(1.0, (divergence * 0.3 + unrelated_ratio * 0.7))
