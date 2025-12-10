import os
import html

from pydantic import BaseModel
from typing import Dict
from pyvis.network import Network
from datetime import datetime
from tools.registry import Tool

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class WorkflowUtils:
    """ Manager to handle workflow execution and visualization."""

    def __init__(self, tools: Dict[str, Tool] = {}):
        self.tools = tools    
    
    def generate_html(self, workflow: BaseModel):
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
            "nodes": {"font": {"size": 14}, "borderWidth": 2, "shadow": true, "shape": "box"},
            "edges": {"arrows": {"to": {"enabled": true}}, "smooth": {"enabled": true, "type": "cubicBezier"}, "width": 2, "shadow": true},
            "physics": {"stabilization": {"iterations": 200}},
            "interaction": {"hover": true, "navigationButtons": true, "keyboard": true}
        }
        """)

        # Add nodes
        for step in workflow_json["steps"]:

            if step["task"]["action"] == "call_tool":
                tool_name = step["task"]["tool_name"]
                task_type = f"Tool({tool_name})"
                color = "#3b82f6"  # Blue for tools
            else:
                task_type = "LLM call"
                color = "#8b5cf6"  # Purple for LLM calls

            params = step.get("parameters", []) or []
            params_text = "\n".join(f"{html.escape(p['key'])}: {html.escape(str(p['value']))}" for p in params) or "None"
            
            results = step.get("results", []) or []
            results_text = "\n".join(html.escape(r['key']) for r in results) or "None"

            title = (
                f"{step['id']}\n"
                f"Type: {task_type}\n\n"
                f"Parameters:\n{params_text}\n\n"
                f"Results:\n{results_text}"
            )

            net.add_node(
                step["id"],
                label=step["id"],
                title=title,
                color=color,
                font={"color": "white"}
            )

        # Add edges
        for i in range(len(workflow_json["steps"]) - 1):
            net.add_edge(workflow_json["steps"][i]["id"], workflow_json["steps"][i + 1]["id"])
    
        # Generate output directory
        results = os.path.join(ROOT, "results")
        os.makedirs(results, exist_ok=True)

        # Create timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = "workflow" + f"_{timestamp}.html"

        # Generate HTML file
        html_str = net.generate_html()
        with open(os.path.join(results, output_file), "w", encoding="utf-8") as f:
            f.write(html_str)