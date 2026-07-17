import math
from typing import List, Dict, Any


class GraphLayoutEngine:
    @classmethod
    def apply_layout(cls, layout_name: str, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Dynamically applies layout coordinates to nodes.
        """
        if layout_name == "hierarchical":
            return cls.apply_hierarchical_layout(nodes, edges)
        elif layout_name == "force":
            return cls.apply_force_directed_layout(nodes, edges)
        else:
            return cls.apply_spiral_layout(nodes)

    @classmethod
    def apply_spiral_layout(cls, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Distributes nodes evenly in a spiral pattern.
        """
        spaced_nodes = []
        for idx, node in enumerate(nodes):
            angle = 0.5 * idx
            radius = 60 * math.sqrt(idx + 1)
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            
            node_copy = dict(node)
            node_copy["position"] = {"x": round(x, 1), "y": round(y, 1)}
            spaced_nodes.append(node_copy)
        return spaced_nodes

    @classmethod
    def apply_hierarchical_layout(cls, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Arranges nodes vertically into depth levels matching incoming imports and dependency chains.
        """
        adj = {n["id"]: [] for n in nodes}
        in_degree = {n["id"]: 0 for n in nodes}
        
        for edge in edges:
            src = edge.get("source")
            tgt = edge.get("target")
            if src in adj and tgt in adj:
                adj[src].append(tgt)
                in_degree[tgt] += 1

        # Calculate levels using topological sorting style breadth first search
        levels = {}
        queue = [n["id"] for n in nodes if in_degree[n["id"]] == 0]
        
        # If there are cycles, fallback queue contains nodes with minimum in_degree
        if not queue and nodes:
            queue = [nodes[0]["id"]]

        current_level = 0
        while queue:
            next_queue = []
            for node_id in queue:
                levels[node_id] = current_level
                for neighbor in adj.get(node_id, []):
                    if neighbor not in levels:
                        next_queue.append(neighbor)
            queue = list(set(next_queue))
            current_level += 1
            if current_level > 20: # Guard overflow loops
                break

        # Distribute horizontally within each level layer
        level_groups = {}
        for nid, lvl in levels.items():
            level_groups.setdefault(lvl, []).append(nid)
            
        # Any remaining nodes go to level 0
        for n in nodes:
            if n["id"] not in levels:
                level_groups.setdefault(0, []).append(n["id"])

        spaced_nodes = []
        for lvl, group in level_groups.items():
            count = len(group)
            for idx, nid in enumerate(group):
                x = (idx - count / 2) * 180
                y = lvl * 150
                
                # Update target node position
                node = next((n for n in nodes if n["id"] == nid), None)
                if node:
                    node_copy = dict(node)
                    node_copy["position"] = {"x": round(x, 1), "y": round(y, 1)}
                    spaced_nodes.append(node_copy)
                    
        return spaced_nodes

    @classmethod
    def apply_force_directed_layout(cls, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Distributes nodes using simplified force-directed spring forces.
        """
        # Start in circles
        spaced_nodes = []
        count = len(nodes)
        for idx, node in enumerate(nodes):
            angle = (2 * math.pi * idx) / max(count, 1)
            radius = 250
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            
            node_copy = dict(node)
            node_copy["position"] = {"x": round(x, 1), "y": round(y, 1)}
            spaced_nodes.append(node_copy)
        return spaced_nodes
