import abc
from typing import List, Dict, Any, Optional


class GraphStorageInterface(abc.ABC):
    @abc.abstractmethod
    async def add_node(
        self,
        node_id: str,
        repository_id: str,
        name: str,
        node_type: str,
        parent_id: Optional[str] = None,
        file_path: Optional[str] = None,
        language: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create or update a node inside the knowledge graph"""
        pass

    @abc.abstractmethod
    async def add_edge(
        self,
        edge_id: str,
        repository_id: str,
        source_id: str,
        target_id: str,
        edge_type: str,
        strength: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create a relationship link between two nodes inside the graph"""
        pass

    @abc.abstractmethod
    async def get_nodes(self, repository_id: str) -> List[Dict[str, Any]]:
        """Retrieve list of all graph nodes for a repository"""
        pass

    @abc.abstractmethod
    async def get_edges(self, repository_id: str) -> List[Dict[str, Any]]:
        """Retrieve list of all graph relationships for a repository"""
        pass

    @abc.abstractmethod
    async def clear_graph(self, repository_id: str) -> None:
        """Purge all node and edge elements associated with a repository"""
        pass
