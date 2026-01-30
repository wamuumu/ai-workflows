"""
Workflow Utilities Module
=========================

This module provides comprehensive workflow management capabilities including
persistence, visualization, and execution tracking. The WorkflowUtils class
serves as the central interface for all workflow I/O operations.

Key Features:
    - Workflow serialization to JSON format
    - Automatic workflow format detection (Linear vs Structured)
    - Interactive graph visualization using PyVis
    - Execution state persistence
    - Run ID management for tracking multiple runs

Directory Structure:
    - data/workflows/: JSON workflow definitions
    - data/visualizations/: Interactive HTML visualizations
    - data/executions/: JSON execution result records

Visualization:
    Workflows are rendered as directed graphs with:
    - Green nodes for initial steps
    - Blue nodes for tool calls
    - Purple nodes for LLM calls
    - Red nodes for final steps
    - Labeled edges showing transition conditions
"""

import os
import html
import json

from pyvis.network import Network
from datetime import datetime
from pydantic import BaseModel

# Compute project root and output directories
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKFLOWS = os.path.join(ROOT, "data", "workflows")
VISUALIZATIONS = os.path.join(ROOT, "data", "visualizations")
EXECUTIONS = os.path.join(ROOT, "data", "executions")


class WorkflowUtils:
    """
    Utility class for workflow persistence and visualization.
    
    Provides static methods for saving, loading, and visualizing
    workflows. Manages run IDs for tracking multiple generation
    and execution runs within a session.
    
    Class Attributes:
        _date: Session date string for filename generation.
        _run_id: Auto-incrementing counter for unique filenames.
    """

    _date = datetime.now().strftime("%Y%m%d%H%M%S")
    _run_id = 1

    @classmethod
    def show(cls, workflow: BaseModel) -> None:
        """
        Display workflow to console.
        
        Args:
            workflow: Pydantic workflow model to display.
        """
        print(workflow.model_dump_json(indent=2))

    @classmethod
    def save_workflow(cls, workflow: BaseModel) -> str:
        """
        Save workflow to JSON file.
        
        Args:
            workflow: Pydantic workflow model to persist.
            
        Returns:
            Absolute path to the saved JSON file.
        """
        
        workflow_json = workflow.model_dump_json(indent=2)
        
        # Create output directory if not exists
        cls._check_folder(WORKFLOWS)

        # Create timestamped filename
        filename = cls._get_filename("workflow", "json")

        # Write to file
        file_path = os.path.join(WORKFLOWS, filename)   
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(workflow_json)
        
        return file_path

    @classmethod
    def load_workflow(cls, filepath: str) -> BaseModel:
        """
        Load workflow from JSON file with automatic format detection.
        
        Determines whether the workflow is Linear or Structured based
        on the presence of transition definitions in steps.
        
        Args:
            filepath: Path to the workflow JSON file.
            
        Returns:
            Appropriate workflow model (LinearWorkflow or StructuredWorkflow).
            
        Raises:
            FileNotFoundError: If workflow file does not exist.
        """

        from models.workflows import LinearWorkflow, StructuredWorkflow
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Workflow file not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            workflow_data = f.read()
        
        workflow_json = json.loads(workflow_data)

        # Detect workflow type by checking for transitions
        steps = workflow_json.get("steps", [])
        has_transitions = any("transitions" in step for step in steps) or any("transition" in step for step in steps)

        if has_transitions:
            return StructuredWorkflow.model_validate(workflow_json)
        else:
            return LinearWorkflow.model_validate(workflow_json)

    @classmethod
    def list_workflows(cls) -> list[str]:
        """
        List all saved workflow files.
        
        Returns:
            List of absolute paths to workflow JSON files.
        """
        
        cls._check_folder(WORKFLOWS)
        return [os.path.join(WORKFLOWS, f) for f in os.listdir(WORKFLOWS) if f.endswith(".json")]

    @classmethod
    def save_visualization(cls, workflow: BaseModel, user_prompt: str) -> str:
        """
        Create interactive HTML visualization of workflow.
        
        Generates a directed graph visualization using PyVis with:
        - Color-coded nodes by step type
        - Hover tooltips with step details
        - Smooth curved edges with condition labels
        - Physics-based layout with stabilization
        
        Args:
            workflow: Pydantic workflow model to visualize.
            user_prompt: Original user request (displayed in header).
            
        Returns:
            Absolute path to the saved HTML visualization.
        """
        
        wf_dict = workflow.model_dump()
        
        # Configure PyVis network with styling
        net = Network(
            width="100%",
            height="98vh",
            directed=True,
            bgcolor="#f8fafc",
            font_color="#111827",
            notebook=False
        )

        # Minimal styling with physics for layout
        net.set_options("""
            {
                "nodes": {
                    "font": {"size": 14},
                    "borderWidth": 2,
                    "shadow": true,
                    "shape": "box"
                },
                "edges": {
                    "arrows": {"to": {"enabled": true}},
                    "smooth": {"enabled": true, "type": "cubicBezier"},
                    "width": 2,
                    "shadow": true
                },
                "physics": {
                    "enabled": true,
                    "stabilization": {
                        "enabled": true,
                        "iterations": 1000,
                        "updateInterval": 25
                    },
                    "solver": "barnesHut",
                    "barnesHut": {
                        "gravitationalConstant": -8000,
                        "centralGravity": 0.3,
                        "springLength": 200,
                        "springConstant": 0.04,
                        "damping": 0.95,
                        "avoidOverlap": 0.2
                    }
                },
                "interaction": {
                    "hover": true,
                    "navigationButtons": true,
                    "keyboard": true
                }
            }
            """
            )

        # Add nodes with type-specific coloring
        for step in wf_dict.get("steps", []):
            
            step_id = step.get("id")
            step_action = step.get("action")
            is_final = step.get("is_final")

            # Determine node color based on step type
            if is_final:
                task_type = "Final Step"
                color = "#ef4444"  # Red for final steps
            elif step_action == "call_tool":
                tool_name = step.get("tool_name")
                tool_parameters = "\n".join(f"  - {html.escape(p.get("key"))}: {html.escape(str(p.get('value')))}" for p in step.get("parameters", [])) or "None"
                task_type = f"Tool({tool_name})"
                color = "#3b82f6"  # Blue for tools
            else:
                task_type = "LLM call"
                prompt = step.get("prompt")
                color = "#8b5cf6"  # Purple for LLM calls
            
            # Override color for first step
            if step_id == 1:
                color = "#10b981"  # Green for the first step

            # Build hover tooltip content
            title = (
                f"Step: {step_id}\n"
                f"Type: {task_type}\n\n"
            )

            if not is_final:
                if step_action == "call_tool":
                    title += f"Tool Name: {html.escape(tool_name)}\nParameters:\n{tool_parameters}\n\n"
                else:
                    title += f"Prompt:\n{html.escape(prompt)}\n\n"

            net.add_node(
                step["id"],
                label=step["id"],
                title=title,
                color=color,
                font={"color": "white"}
            )

        # Add edges based on transitions or sequential order
        for step in wf_dict.get("steps", []):
            step_id = step.get("id")
            is_final = step.get("is_final")
            if not is_final:
                # Check for transitions (Tool call have only one transition)
                transitions = step.get("transitions", []) or [step.get("transition", None)]
                if transitions:
                    # Structured workflow: explicit transitions
                    for transition in transitions:
                        if transition:
                            next = transition.get("next_step")
                            if next in net.node_ids:
                                net.add_edge(step_id, transition.get("next_step"), label=transition.get("condition"))
                else:
                    # Linear workflow: implicit sequential flow
                    if step_id + 1 in net.node_ids:
                        net.add_edge(step_id, step_id + 1)
    
        # Create output directory if not exists
        cls._check_folder(VISUALIZATIONS)

        # Create timestamped filename
        filename = cls._get_filename("workflow", "html")

        # Generate HTML and inject user prompt header
        html_str = net.generate_html()
        prompt_block = f"""
            <div style="position: absolute; z-index: 1; margin: 10;">
                <strong>User Prompt:</strong> {html.escape(user_prompt)}
            </div>
        """
        html_str = html_str.replace(
            '<div id="mynetwork" class="card-body"></div>',
            prompt_block + '\n<div id="mynetwork" class="card-body"></div>',
            1
        )
        file_path = os.path.join(VISUALIZATIONS, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_str)
        
        return file_path

    @classmethod
    def save_execution(cls, execution_data: dict) -> str:
        """
        Save workflow execution results to JSON file.
        
        Args:
            execution_data: Dict mapping step IDs to execution outputs.
            
        Returns:
            Absolute path to the saved execution file.
        """
        
        execution_json = json.dumps(execution_data, indent=2)
        
        # Create output directory if not exists
        cls._check_folder(EXECUTIONS)

        # Create timestamped filename
        filename = cls._get_filename("execution", "json")

        # Write to file
        file_path = os.path.join(EXECUTIONS, filename)   
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(execution_json)
        
        return file_path

    @classmethod
    def load_execution(cls, filepath: str) -> dict:
        """
        Load workflow execution results from JSON file.
        
        Args:
            filepath: Path to the execution JSON file.
            
        Returns:
            Dict containing execution data (step_id → output).
        """
        
        with open(filepath, "r", encoding="utf-8") as f:
            execution_data = json.load(f)

        return execution_data

    @classmethod
    def _check_folder(cls, folder_path: str):
        """
        Ensure the specified folder exists.
        
        Args:
            folder_path: Directory path to create if missing.
        """
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    @classmethod
    def _get_filename(cls, prefix: str, extension: str) -> str:
        """
        Generate a timestamped filename.
        
        Args:
            prefix: Filename prefix (e.g., "workflow", "execution").
            extension: File extension without dot (e.g., "json", "html").
            
        Returns:
            Filename in format: {prefix}_{date}_{run_id}.{extension}
        """
        return f"{prefix}_{cls._date}_{cls._run_id}.{extension}"

    @classmethod
    def increment_run_id(cls):
        """
        Increment the run ID counter.
        
        Called after each workflow save to ensure unique filenames.
        """
        cls._run_id += 1
    
    @classmethod
    def set_run_id(cls, run_id: int):
        """
        Set the run ID counter to a specific value.
        
        Used when loading existing workflows to maintain ID continuity.
        
        Args:
            run_id: The run ID value to set.
        """
        cls._run_id = run_id