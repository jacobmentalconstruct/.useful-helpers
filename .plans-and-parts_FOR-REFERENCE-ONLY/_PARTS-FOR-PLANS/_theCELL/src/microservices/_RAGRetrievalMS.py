"""
SERVICE_NAME: _RAGRetrievalMS
ROLE: Retrieval Domain — query → embed → search → formatted context string.
Pure read path. Takes FaissStore and IngestEngineMS as injected parameters.
Does NOT know about SessionData, Backend, UI, signals, or ingest logic.
"""
import logging
from typing import List, Dict, Any

from .base_service import BaseService
from .microservice_std_lib import service_metadata


@service_metadata(
    name='RAGRetrieval',
    version='1.0.0',
    description='Retrieval domain: embeds a query, searches an injected FaissStore, returns a formatted context string.',
    tags=['retrieval', 'rag', 'search'],
    capabilities=['semantic-search', 'context-formatting'],
    internal_dependencies=['_IngestEngineMS', 'base_service', 'microservice_std_lib'],
    external_dependencies=[],
)
class RAGRetrievalMS(BaseService):

    def __init__(self, ingest_engine):
        """
        ingest_engine: IngestEngineMS instance (for _get_embedding on query text)
        """
        super().__init__('RAGRetrieval')
        self.ingest_engine = ingest_engine

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def retrieve(self, query: str, store, embed_model: str, k: int = 5) -> str:
        """
        Embed query, search store, return formatted context string.
        Returns "" if store is empty, embedding fails, or no results found.
        """
        try:
            if store.count() == 0:
                return ""
            vec = self.ingest_engine._get_embedding(embed_model, query)
            if vec is None:
                return ""
            results = store.search(vec, k)
            return self._format_context(results)
        except Exception as e:
            self.logger.error(f"RAG retrieval failed: {e}")
            return ""

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _format_context(self, results: List[Dict]) -> str:
        """Format search results into a labelled context block."""
        if not results:
            return ""
        lines = ["### RETRIEVED CONTEXT ###"]
        for i, item in enumerate(results, start=1):
            meta = item.get('metadata', item)
            source = meta.get('source_file', 'unknown')
            kind = meta.get('type', '')
            name = meta.get('name', '')
            content = meta.get('content', '')
            label = f"[{i}] {source}"
            if kind:
                label += f" ({kind}"
                if name:
                    label += f": {name}"
                label += ")"
            lines.append(label + ":")
            lines.append(content)
            lines.append("")
        return "\n".join(lines).rstrip()
