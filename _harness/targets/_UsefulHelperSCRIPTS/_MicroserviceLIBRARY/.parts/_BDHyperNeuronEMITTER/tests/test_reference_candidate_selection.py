import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


EMITTER_SRC = Path(__file__).resolve().parents[1] / "src"
if str(EMITTER_SRC) not in sys.path:
    sys.path.insert(0, str(EMITTER_SRC))

from core.assembler.core import GraphAssembler
from core.contract.hyperhunk import HyperHunk


class RecordingNucleus:
    def __init__(self) -> None:
        self.pairs: list[tuple[str, str]] = []

    def evaluate(self, a, b):
        self.pairs.append((a.occurrence_id, b.occurrence_id))
        return SimpleNamespace(
            connection_strength=0.0,
            routing_profile={
                "grammatical": 0.0,
                "structural": 0.0,
                "statistical": 0.0,
                "semantic": 0.0,
                "verbatim": 0.0,
            },
            interaction_type="multi_surface",
            interaction_vector=[0.0, 0.0, 0.0, 0.0, 0.0],
            above_threshold=False,
        )


def _make_hunk(
    *,
    content: str,
    origin_id: str,
    node_kind: str,
    structural_path: str,
    heading_trail=None,
    normalized_cross_refs=None,
):
    return HyperHunk(
        content=content,
        origin_id=origin_id,
        layer_type="CST",
        node_kind=node_kind,
        structural_path=structural_path,
        heading_trail=list(heading_trail or []),
        normalized_cross_refs=list(normalized_cross_refs or []),
        token_count=max(1, len(content.split())),
    )


class ReferenceCandidateSelectionTests(unittest.TestCase):
    def test_reference_candidates_can_reach_beyond_sliding_window(self):
        index_item = _make_hunk(
            content="* 2. Lexical analysis",
            origin_id="memory://index.txt",
            node_kind="md_list_item",
            structural_path="doc/h1_reference/li_4",
            normalized_cross_refs=["lexical_analysis"],
        )
        filler_one = _make_hunk(
            content="filler one",
            origin_id="memory://filler1.txt",
            node_kind="md_paragraph",
            structural_path="doc/h1_misc/p1",
        )
        filler_two = _make_hunk(
            content="filler two",
            origin_id="memory://filler2.txt",
            node_kind="md_paragraph",
            structural_path="doc/h1_misc/p2",
        )
        target = _make_hunk(
            content="2. Lexical analysis",
            origin_id="memory://lexical_analysis.txt",
            node_kind="md_heading",
            structural_path="doc/h1_lexical_analysis",
            heading_trail=["Lexical analysis"],
        )

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "cold.db"

            baseline_nucleus = RecordingNucleus()
            with GraphAssembler(
                db_path,
                baseline_nucleus,
                window_size=2,
                reference_candidate_limit=0,
            ) as assembler:
                for hunk in [index_item, filler_one, filler_two, target]:
                    assembler.ingest_one(hunk)

            baseline_pairs = set(baseline_nucleus.pairs)
            self.assertNotIn((index_item.occurrence_id, target.occurrence_id), baseline_pairs)

            indexed_nucleus = RecordingNucleus()
            with GraphAssembler(
                db_path,
                indexed_nucleus,
                window_size=2,
                reference_candidate_limit=8,
            ) as assembler:
                for hunk in [index_item, filler_one, filler_two, target]:
                    assembler.ingest_one(hunk)

            indexed_pairs = set(indexed_nucleus.pairs)
            self.assertIn((index_item.occurrence_id, target.occurrence_id), indexed_pairs)

    def test_anchor_registry_prefers_heading_anchor_over_weaker_reference_match(self):
        weaker_candidate = _make_hunk(
            content="* lexical analysis",
            origin_id="memory://index_b.txt",
            node_kind="md_list_item",
            structural_path="doc/h1_reference/li_8",
            normalized_cross_refs=["lexical_analysis"],
        )
        filler_one = _make_hunk(
            content="filler one",
            origin_id="memory://filler1.txt",
            node_kind="md_paragraph",
            structural_path="doc/h1_misc/p1",
        )
        filler_two = _make_hunk(
            content="filler two",
            origin_id="memory://filler2.txt",
            node_kind="md_paragraph",
            structural_path="doc/h1_misc/p2",
        )
        stronger_candidate = _make_hunk(
            content="2. Lexical analysis",
            origin_id="memory://lexical_analysis.txt",
            node_kind="md_heading",
            structural_path="doc/h1_lexical_analysis",
            heading_trail=["Lexical analysis"],
        )
        incoming_index = _make_hunk(
            content="* 2. Lexical analysis",
            origin_id="memory://index_a.txt",
            node_kind="md_list_item",
            structural_path="doc/h1_reference/li_4",
            normalized_cross_refs=["lexical_analysis"],
        )

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "cold.db"
            nucleus = RecordingNucleus()
            with GraphAssembler(
                db_path,
                nucleus,
                window_size=2,
                reference_candidate_limit=1,
            ) as assembler:
                for hunk in [stronger_candidate, weaker_candidate, filler_one, filler_two, incoming_index]:
                    assembler.ingest_one(hunk)

            pairs = set(nucleus.pairs)
            self.assertIn((stronger_candidate.occurrence_id, incoming_index.occurrence_id), pairs)
            self.assertNotIn((weaker_candidate.occurrence_id, incoming_index.occurrence_id), pairs)

    def test_common_anchor_terms_are_suppressed_after_threshold(self):
        common_a = _make_hunk(
            content="Common",
            origin_id="memory://common_a.txt",
            node_kind="md_heading",
            structural_path="doc/h1_common_a",
            heading_trail=["Common"],
        )
        common_b = _make_hunk(
            content="Common",
            origin_id="memory://common_b.txt",
            node_kind="md_heading",
            structural_path="doc/h1_common_b",
            heading_trail=["Common"],
        )
        filler_one = _make_hunk(
            content="filler one",
            origin_id="memory://filler1.txt",
            node_kind="md_paragraph",
            structural_path="doc/h1_misc/p1",
        )
        filler_two = _make_hunk(
            content="filler two",
            origin_id="memory://filler2.txt",
            node_kind="md_paragraph",
            structural_path="doc/h1_misc/p2",
        )
        incoming_index = _make_hunk(
            content="* Common",
            origin_id="memory://index.txt",
            node_kind="md_list_item",
            structural_path="doc/h1_reference/li_4",
            normalized_cross_refs=["common"],
        )

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "cold.db"
            nucleus = RecordingNucleus()
            with GraphAssembler(
                db_path,
                nucleus,
                window_size=2,
                reference_candidate_limit=8,
                anchor_common_term_threshold=1,
            ) as assembler:
                for hunk in [common_a, common_b, filler_one, filler_two, incoming_index]:
                    assembler.ingest_one(hunk)

            pairs = set(nucleus.pairs)
            self.assertNotIn((common_a.occurrence_id, incoming_index.occurrence_id), pairs)
            self.assertNotIn((common_b.occurrence_id, incoming_index.occurrence_id), pairs)


if __name__ == "__main__":
    unittest.main()
