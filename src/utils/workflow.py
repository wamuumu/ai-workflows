import os
import html
import uuid
import json

from pyvis.network import Network
from datetime import datetime
from pydantic import BaseModel

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKFLOWS = os.path.join(ROOT, "data", "workflows")
VISUALIZATIONS = os.path.join(ROOT, "data", "visualizations")
EXECUTIONS = os.path.join(ROOT, "data", "executions")

class WorkflowUtils:
    """Utility class for managing workflows."""

    _run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    @classmethod
    def show(cls, workflow: BaseModel) -> None:
        """Display the workflow structure."""
        print(workflow.model_dump_json(indent=2))

    @classmethod
    def save_workflow(cls, workflow: BaseModel) -> str:
        """Save the workflow as a JSON file."""
        
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
    def load_workflow(cls, filepath: str, model: BaseModel) -> BaseModel:
        """Load a workflow from a JSON file into the specified model format."""
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Workflow file not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            workflow_data = f.read()

        return model.model_validate_json(workflow_data)

    @classmethod
    def list_workflows(cls) -> list[str]:
        """List all saved workflows."""
        
        cls._check_folder(WORKFLOWS)
        return [os.path.join(WORKFLOWS, f) for f in os.listdir(WORKFLOWS) if f.endswith(".json")]

    @classmethod
    def save_visualization(cls, workflow: BaseModel) -> str:
        """Create a visual representation of the workflow using pyvis."""
        
        workflow_json = workflow.model_dump()
        
        net = Network(
            width="100%",
            height="98vh",
            directed=True,
            bgcolor="#f8fafc",
            font_color="#111827",
            notebook=False
        )

        # Minimal styling
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

        # Add nodes
        for step in workflow_json["steps"]:
            
            is_final = "is_final" in step and step["is_final"]
            if is_final:
                task_type = "Final Step"
                color = "#ef4444"  # Red for final steps
            elif step["action"] == "call_tool":
                tool_name = step["tool_name"]
                tool_parameters = "\n".join(f"{html.escape(p['key'])}: {html.escape(str(p['value']))}" for p in step["parameters"]) or "None"
                task_type = f"Tool({tool_name})"
                color = "#3b82f6"  # Blue for tools
            else:
                task_type = "LLM call"
                prompt = step["prompt"]
                color = "#8b5cf6"  # Purple for LLM calls
            
            if step["id"] == "step_1":
                color = "#10b981"  # Green for the first step

            title = (
                f"{step['id']}\n"
                f"Type: {task_type}\n\n"
            )

            if not is_final and step["action"] == "call_tool":
                title += f"Tool Name: {html.escape(tool_name)}\nParameters:\n{tool_parameters}\n\n"
            elif not is_final and step["action"] == "call_llm":
                title += f"Prompt:\n{html.escape(prompt)}\n\n"

            net.add_node(
                step["id"],
                label=step["id"],
                title=title,
                color=color,
                font={"color": "white"}
            )

        # Add edges
        if workflow.__class__.__name__ == "StructuredWorkflow":
            for step in workflow_json["steps"]:
                is_final = "is_final" in step and step["is_final"]
                if not is_final:
                    for transition in step["transitions"]:
                        net.add_edge(step["id"], transition["next_step"], label=transition["condition"])
        else:
            # Linear workflow
            for i in range(len(workflow_json["steps"]) - 1):
                is_final = "is_final" in workflow_json["steps"][i] and workflow_json["steps"][i]["is_final"]
                if not is_final:
                    net.add_edge(workflow_json["steps"][i]["id"], workflow_json["steps"][i + 1]["id"])
    
        # Create output directory if not exists
        cls._check_folder(VISUALIZATIONS)

        # Create timestamped filename
        filename = cls._get_filename("workflow", "html")

        # Generate HTML file and save
        html_str = net.generate_html()
        file_path = os.path.join(VISUALIZATIONS, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_str)
        
        return file_path

    @classmethod
    def save_execution(cls, execution_data: dict) -> str:
        """Save the workflow execution data as a JSON file."""
        
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
        """Load a workflow execution from a JSON file."""
        
        with open(filepath, "r", encoding="utf-8") as f:
            execution_data = json.load(f)

        return execution_data

    @classmethod
    def _check_folder(cls, folder_path: str):
        """Ensure the specified folder exists; create it if it doesn't."""
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    @classmethod
    def _get_filename(cls, prefix: str, extension: str) -> str:
        """Generate a timestamped filename."""
        return f"{prefix}_{cls._run_id}_{uuid.uuid4().hex}.{extension}"