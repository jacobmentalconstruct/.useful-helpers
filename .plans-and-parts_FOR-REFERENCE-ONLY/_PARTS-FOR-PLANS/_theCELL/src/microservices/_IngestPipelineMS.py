"""
SERVICE_NAME: _IngestPipelineMS
ROLE: Ingest Domain — file → chunk → embed → store.
Takes FaissStore as an injected parameter; does NOT own it.
Does NOT know about SessionData, Backend, UI, or signals.
"""
import os
import logging
from typing import List, Dict, Any

from .base_service import BaseService
from .microservice_std_lib import service_metadata


@service_metadata(
    name='IngestPipeline',
    version='1.0.0',
    description='Ingest domain: reads files, chunks with SemanticChunkerMS, embeds via IngestEngineMS, writes to an injected FaissStore.',
    tags=['ingest', 'pipeline', 'rag'],
    capabilities=['file-ingest', 'directory-ingest', 'semantic-chunking'],
    internal_dependencies=['_SemanticChunkerMS', '_IngestEngineMS', 'base_service', 'microservice_std_lib'],
    external_dependencies=[],
)
class IngestPipelineMS(BaseService):

    def __init__(self, chunker, ingest_engine):
        """
        chunker      : SemanticChunkerMS instance
        ingest_engine: IngestEngineMS instance (for _get_embedding)
        """
        super().__init__('IngestPipeline')
        self.chunker = chunker
        self.ingest_engine = ingest_engine

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest_file(self, file_path: str, store, embed_model: str) -> Dict[str, Any]:
        """
        Read one file, chunk it, embed each chunk, add to store.
        Returns: { 'file': str, 'chunks_added': int, 'skipped': int }
        """
        chunks_added = 0
        skipped = 0
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except OSError as e:
            self.logger.error(f"Cannot read {file_path}: {e}")
            return {'file': file_path, 'chunks_added': 0, 'skipped': 0}

        filename = os.path.basename(file_path)
        chunks = self.chunker.chunk_file(content, filename)

        for chunk in chunks:
            vec = self.ingest_engine._get_embedding(embed_model, chunk['content'])
            if vec is None:
                skipped += 1
                continue
            meta = {
                'source_file': file_path,
                'name': chunk.get('name', ''),
                'type': chunk.get('type', ''),
                'start_line': chunk.get('start_line', 0),
                'end_line': chunk.get('end_line', 0),
                'content': chunk['content'][:2000],
            }
            store.add([vec], [meta])
            chunks_added += 1

        self.logger.info(f"Ingested '{filename}': {chunks_added} chunks added, {skipped} skipped.")
        return {'file': file_path, 'chunks_added': chunks_added, 'skipped': skipped}

    def ingest_directory(
        self,
        dir_path: str,
        extensions: List[str],
        store,
        embed_model: str,
    ) -> Dict[str, Any]:
        """
        Walk dir_path, ingest all files matching extensions.
        Returns: { 'files_processed': int, 'total_chunks_added': int }
        """
        ext_set = {e.lower() if e.startswith('.') else f'.{e.lower()}' for e in extensions}
        files_processed = 0
        total_chunks = 0

        for root, _, files in os.walk(dir_path):
            for fname in files:
                _, ext = os.path.splitext(fname)
                if ext.lower() not in ext_set:
                    continue
                full_path = os.path.join(root, fname)
                stats = self.ingest_file(full_path, store, embed_model)
                files_processed += 1
                total_chunks += stats['chunks_added']

        self.logger.info(f"Directory ingest complete: {files_processed} files, {total_chunks} chunks.")
        return {'files_processed': files_processed, 'total_chunks_added': total_chunks}
