import io
import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace


EMITTER_SRC = Path(__file__).resolve().parents[1] / "src"
if str(EMITTER_SRC) not in sys.path:
    sys.path.insert(0, str(EMITTER_SRC))

import app as emitter_app
from core.assembler.core import GraphAssembler
from core.contract.hyperhunk import HyperHunk
from core.engine.inference.bag_view import build_bag


class AlwaysOnNucleus:
    def evaluate(self, a, b):
        return SimpleNamespace(
            connection_strength=0.5,
            routing_profile={
                "grammatical": 0.2,
                "structural": 0.5,
                "statistical": 0.2,
                "semantic": 0.0,
                "verbatim": 0.1,
            },
            interaction_type="structural_bridge",
            interaction_vector=[0.2, 0.5, 0.2, 0.0, 0.1],
            above_threshold=True,
        )


def _make_hunk(*, content: str, origin_id: str, node_kind: str, structural_path: str):
    return HyperHunk(
        content=content,
        origin_id=origin_id,
        layer_type="CST",
        node_kind=node_kind,
        structural_path=structural_path,
        token_count=max(1, len(content.split())),
    )


class BagViewTests(unittest.TestCase):
    def _build_fixture_db(self, db_path: Path) -> tuple[HyperHunk, HyperHunk]:
        list_item = _make_hunk(
            content="* 2. Lexical analysis",
            origin_id="memory://index.txt",
            node_kind="md_list_item",
            structural_path="doc/h1_reference/li_4",
        )
        heading = _make_hunk(
            content="2. Lexical analysis",
            origin_id="memory://lexical_analysis.txt",
            node_kind="md_heading",
            structural_path="doc/h1_2_lexical_analysis",
        )

        with GraphAssembler(db_path, AlwaysOnNucleus(), window_size=10) as assembler:
            assembler.ingest_one(list_item)
            assembler.ingest_one(heading)

        return list_item, heading

    def test_build_bag_returns_grouped_pullback_ready_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "cold.db"
            list_item, heading = self._build_fixture_db(db_path)

            bag = build_bag(
                query_text="lexical analysis",
                db_path=db_path,
                top_k=5,
                group_by="origin_id",
                pull_occurrence_ids=[heading.occurrence_id],
            )

        self.assertEqual(bag["query"], "lexical analysis")
        self.assertGreaterEqual(bag["bag_summary"]["item_count"], 2)
        self.assertEqual(bag["bag_summary"]["group_by"], "origin_id")
        self.assertGreaterEqual(bag["bag_summary"]["group_count"], 2)

        item_ids = {item["occurrence_id"] for item in bag["items"]}
        self.assertIn(list_item.occurrence_id, item_ids)
        self.assertIn(heading.occurrence_id, item_ids)

        pull_ids = bag["pullback"]["selected_occurrence_ids"]
        self.assertEqual(pull_ids, [heading.occurrence_id])
        self.assertIn("Lexical analysis", bag["pullback"]["items"][0]["pullback_text"])

        first_item = bag["items"][0]
        self.assertIn("item_summary", first_item)
        self.assertIn("why", first_item)

    def test_cmd_bag_emits_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "cold.db"
            _, heading = self._build_fixture_db(db_path)

            args = Namespace(
                query="lexical analysis",
                db=str(db_path),
                top_k=5,
                hop_limit=2,
                decay=0.9,
                group_by="origin_id",
                include_full_text=False,
                pull_occurrence_id=[heading.occurrence_id],
                embedder_override=None,
                sentence_model=None,
            )

            stdout = io.StringIO()
            original_stdout = sys.stdout
            try:
                sys.stdout = stdout
                rc = emitter_app.cmd_bag(args)
            finally:
                sys.stdout = original_stdout

        self.assertEqual(rc, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["query"], "lexical analysis")
        self.assertEqual(payload["pullback"]["selected_occurrence_ids"], [heading.occurrence_id])


if __name__ == "__main__":
    unittest.main()
