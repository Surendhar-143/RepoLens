from typing import List, Dict, Any, Optional
import math


class DocumentationEngine:
    @classmethod
    def generate_readme(cls, repo_name: str, tech_stack: List[str], folder_structure: List[str]) -> str:
        """
        Generate or enrich repository README file.
        """
        tech_list = "\n".join([f"* **{tech}**" for tech in tech_stack]) if tech_stack else "* **Vanilla JS/Python**"
        folder_list = "\n".join([f"* `{path}`" for path in folder_structure[:8]])
        
        readme = (
            f"# {repo_name}\n\n"
            f"AI-powered structural code intelligence platform.\n\n"
            f"## Technology Stack\n"
            f"{tech_list}\n\n"
            f"## Repository Structure\n"
            f"Below is a preview of the main folder entrypoints:\n"
            f"{folder_list}\n\n"
            f"## Development & Setup\n"
            f"1. **Build Environment**: Clone and install dependencies.\n"
            f"2. **Run Dev server**: Start local configurations configurations.\n"
        )
        return readme

    @classmethod
    def generate_architecture_guide(cls, repo_name: str, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> str:
        """
        Synthesize architecture document with embedded Mermaid package graphs.
        """
        # Build Mermaid graph
        mermaid_lines = ["graph TD"]
        for node in nodes[:15]: # Limit to avoid canvas layout blowups
            label = node.get("name", node.get("label", node["id"]))
            mermaid_lines.append(f'  {node["id"]}["{label}"]')
        for edge in edges[:15]:
            mermaid_lines.append(f'  {edge["source"]} --> {edge["target"]}')
            
        mermaid_graph = "\n".join(mermaid_lines)

        guide = (
            f"# Technical Architecture Guide for {repo_name}\n\n"
            f"This document outlines high-level packages layout and structural flows.\n\n"
            f"## Package Interactions Map\n"
            f"```mermaid\n"
            f"{mermaid_graph}\n"
            f"```\n\n"
            f"## Architectural Observations\n"
            f"* **Decoupled Monolith**: Modules communicate through clean API boundaries.\n"
            f"* **Flows Routing**: Controllers query ORM entities directly.\n"
        )
        return guide

    @classmethod
    def generate_api_reference(cls, repo_name: str, flows: List[Dict[str, Any]]) -> str:
        """
        Construct endpoint routing guides.
        """
        endpoint_blocks = []
        for flow in flows:
            method = flow.get("method", "GET")
            path = flow.get("route_path", "/")
            controller = flow.get("controller_name", "Handler")
            models_list = ", ".join([m.get("model_name", "Model") for m in flow.get("database_models", [])])
            
            block = (
                f"### `{method}` {path}\n"
                f"* **Controller Handler**: `{controller}`\n"
                f"* **Database Interactions**: {models_list if models_list else 'None'}\n"
            )
            endpoint_blocks.append(block)

        endpoints_str = "\n".join(endpoint_blocks) if endpoint_blocks else "*No HTTP API paths detected.*"

        api_ref = (
            f"# REST API Reference Manual\n\n"
            f"List of controllers, endpoint parameters, and validations found in {repo_name}.\n\n"
            f"{endpoints_str}\n"
        )
        return api_ref

    @classmethod
    def generate_database_guide(cls, repo_name: str, nodes: List[Dict[str, Any]]) -> str:
        """
        Create database ER schemas summary.
        """
        model_nodes = [n for n in nodes if n.get("type") == "model"]
        
        # Build ER Mermaid
        er_lines = ["erDiagram"]
        for model in model_nodes[:10]:
            name = model.get("name", "Model")
            er_lines.append(f"  {name} ||--o{{ Details : interacts")
            
        er_diagram = "\n".join(er_lines) if model_nodes else "%% No models detected"

        db_guide = (
            f"# Database ER Schema Manual\n\n"
            f"Scanned Entity Relationships for {repo_name}.\n\n"
            f"## ER Diagram\n"
            f"```mermaid\n"
            f"{er_diagram}\n"
            f"```\n\n"
            f"## Mapped Models\n"
        )
        
        for model in model_nodes:
            name = model.get("name", "Model")
            db_guide += f"* **{name}**: Mapped database properties schema node.\n"
            
        return db_guide
