import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


EMITTER_SRC = Path(__file__).resolve().parents[1] / "src"
if str(EMITTER_SRC) not in sys.path:
    sys.path.insert(0, str(EMITTER_SRC))

from core.engine.inference.provider import (
    EmbeddingProviderSpec,
    load_embedding_provider_spec,
    query,
    save_embedding_provider_spec,
)
from core.engine.inference.retrieval import AnchorResult


class _FakeEmbedProvider:
    def embed_texts(self, texts):
        return type(
            "EmbedResultLike",
            (),
            {
                "vectors": [[1.0, 0.0] for _ in texts],
                "dimensions": 2,
                "token_counts": [len(t.split()) for t in texts],
                "token_ids": [[] for _ in texts],
            },
        )()


class _FakeHotEngine:
    def __init__(self, decay: float, hop_limit: int) -> None:
        self.decay = decay
        self.hop_limit = hop_limit

    def run(self, subgraph, anchor_ids, top_k: int = 20):
        return [
            type(
                "BagResult",
                (),
                {
                    "occurrence_id": anchor_ids[0],
                    "hunk_id": "h1",
                    "node_kind": "md_paragraph",
                    "activation": 0.91,
                    "attention_weight": 1.0,
                    "static_mass": 10,
                },
            )()
        ]


class EmbeddingProviderTests(unittest.TestCase):
    def test_provider_spec_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            saved = save_embedding_provider_spec(
                output_dir,
                EmbeddingProviderSpec(
                    provider="sentence-transformers",
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    artifacts_dir="",
                ),
            )
            self.assertTrue(saved.is_file())
            loaded = load_embedding_provider_spec(output_dir / "cold.db")
            self.assertEqual(loaded.provider, "sentence-transformers")
            self.assertEqual(loaded.model_name, "sentence-transformers/all-MiniLM-L6-v2")

    def test_query_uses_sentence_provider_metadata_for_ann(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "cold.db"
            db_path.touch()
            save_embedding_provider_spec(
                db_path.parent,
                EmbeddingProviderSpec(
                    provider="sentence-transformers",
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                ),
            )

            anchors = [
                AnchorResult(
                    occurrence_id="occ-1",
                    hunk_id="h1",
                    score=0.88,
                    origin_id="memory://doc.txt",
                    node_kind="md_paragraph",
                    content_snippet="semantic result",
                )
            ]

            with patch(
                "core.engine.inference.provider.create_embed_provider",
                return_value=_FakeEmbedProvider(),
            ) as create_provider, patch(
                "core.engine.inference.retrieval.fts_search",
                return_value=[],
            ), patch(
                "core.engine.inference.retrieval.ann_search",
                return_value=anchors,
            ) as ann_search, patch(
                "core.engine.inference.retrieval.load_subgraph",
                return_value={"nodes": {}, "edges": [], "inhibit_occ_pairs": []},
            ), patch(
                "core.engine.inference.hot_engine.HotEngine",
                _FakeHotEngine,
            ):
                results = query("semantic check", db_path=db_path, top_k=5)

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].occurrence_id, "occ-1")
            create_provider.assert_called_once()
            ann_search.assert_called_once()


if __name__ == "__main__":
    unittest.main()
