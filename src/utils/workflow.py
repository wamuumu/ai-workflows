import os
import html
import uuid

from pyvis.network import Network
from datetime import datetime
from pydantic import BaseModel

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKFLOWS = os.path.join(ROOT, "data", "workflows")
VISUALIZATIONS = os.path.join(ROOT, "data", "visualizations")

class WorkflowUtils:
    """Utility class for managing workflows."""

    _run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    @classmethod
    def show(cls, workflow: BaseModel) -> None:
        """Display the workflow structure."""
        print(workflow.model_dump_json(indent=2))

    @classmethod
    def save_json(cls, workflow: BaseModel) -> str:
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
    def load_json(cls, filepath: str, model: BaseModel) -> BaseModel:
        """Load a workflow from a JSON file into the specified model format."""
        
        with open(filepath, "r", encoding="utf-8") as f:
            workflow_data = f.read()

        return model.model_validate_json(workflow_data)

    @classmethod
    def save_html(cls, workflow: BaseModel) -> str:
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

            if step["action"] == "call_tool":
                tool_name = step["tool_name"]
                task_type = f"Tool({tool_name})"
                color = "#3b82f6"  # Blue for tools
            else:
                task_type = "LLM call"
                color = "#8b5cf6"  # Purple for LLM calls

            params = step["parameters"] or []
            params_text = "\n".join(f"{html.escape(p['key'])}: {html.escape(str(p['value']))}" for p in params) or "None"

            title = (
                f"{step['id']}\n"
                f"Type: {task_type}\n\n"
                f"Parameters:\n{params_text}\n\n"
            )

            net.add_node(
                step["id"],
                label=step["id"],
                title=title,
                color=color,
                font={"color": "white"}
            )

        # Add edges
        has_transitions = any("transitions" in step for step in workflow_json["steps"])
        if has_transitions:
            # Non-linear workflow with explicit transitions
            for step in workflow_json["steps"]:
                transitions = step["transitions"] or []
                if len(transitions) == 1:
                    net.add_edge(step["id"], transitions[0]["next_step"])
                else:
                    for transition in transitions:
                        net.add_edge(step["id"], transition["next_step"], label=transition["condition"])
        else:
            # Linear workflow
            for i in range(len(workflow_json["steps"]) - 1):
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
    def _check_folder(cls, folder_path: str):
        """Ensure the specified folder exists; create it if it doesn't."""
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    @classmethod
    def _get_filename(cls, prefix: str, extension: str) -> str:
        """Generate a timestamped filename."""
        return f"{prefix}_{cls._run_id}_{uuid.uuid4().hex}.{extension}"