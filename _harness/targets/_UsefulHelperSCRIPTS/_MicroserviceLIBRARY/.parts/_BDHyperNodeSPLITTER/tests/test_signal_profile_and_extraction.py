import sys
import unittest
from pathlib import Path


SPLITTER_SRC = Path(__file__).resolve().parents[1] / "src"
if str(SPLITTER_SRC) not in sys.path:
    sys.path.insert(0, str(SPLITTER_SRC))

from core.contract.hyperhunk import HyperHunk
from core.engines.peg_eng import PEGEngine
from core.negotiator import Negotiator
from core.signal_profile import SplitterSignalProfile


class SplitterSignalProfileTests(unittest.TestCase):
    def test_default_profile_round_trip(self):
        profile = SplitterSignalProfile.default()
        clone = SplitterSignalProfile.from_dict(profile.to_dict())
        self.assertEqual(profile.to_dict(), clone.to_dict())

    def test_unknown_keys_rejected(self):
        payload = SplitterSignalProfile.default().to_dict()
        payload["bogus"] = {}
        with self.assertRaises(ValueError):
            SplitterSignalProfile.from_dict(payload)

    def test_invalid_threshold_rejected(self):
        payload = SplitterSignalProfile.default().to_dict()
        payload["structured_text_profile"]["heading_pair_threshold"] = 0
        with self.assertRaises(ValueError):
            SplitterSignalProfile.from_dict(payload)


class SplitterExtractionTests(unittest.TestCase):
    def test_rest_references_are_normalized_deterministically(self):
        profile = SplitterSignalProfile.default()
        engine = PEGEngine(signal_profile=profile)
        text = (
            "Execution model\n"
            "===============\n\n"
            "See :doc:`reference/import`, :ref:`the import system <import-system>` "
            "and ``file_input``.\n"
        )
        hunks = list(engine.parse(text, "memory://reference/executionmodel.txt"))
        paragraph = next(h for h in hunks if h.node_kind == "md_paragraph")
        self.assertEqual(
            paragraph.normalized_cross_refs,
            ["reference/import", "import_system", "file_input"],
        )
        self.assertEqual(
            sorted(paragraph.reference_kinds),
            ["grammar_symbol", "rst_doc", "rst_ref"],
        )
        self.assertGreaterEqual(paragraph.reference_confidence, 0.45)
        self.assertTrue(paragraph.metadata["reference_records"])

    def test_noisy_inline_code_is_not_promoted_to_reference(self):
        profile = SplitterSignalProfile.default()
        engine = PEGEngine(signal_profile=profile)
        text = (
            "Notes\n"
            "=====\n\n"
            "Use `x + y` inside code and keep `tmp` local.\n"
        )
        hunks = list(engine.parse(text, "memory://notes.txt"))
        paragraph = next(h for h in hunks if h.node_kind == "md_paragraph")
        self.assertEqual(paragraph.normalized_cross_refs, [])
        self.assertEqual(paragraph.reference_confidence, 0.0)

    def test_list_items_can_emit_as_distinct_hunks(self):
        profile = SplitterSignalProfile.from_dict({
            "structured_text_profile": SplitterSignalProfile.default().structured_text_profile.to_dict(),
            "reference_extraction_profile": SplitterSignalProfile.default().reference_extraction_profile.to_dict(),
            "list_representation_profile": {
                "emit_list_items": True,
                "max_list_item_length": 320,
                "preserve_markers": False,
                "inherit_heading_ancestry": True,
            },
            "fragment_inheritance_profile": SplitterSignalProfile.default().fragment_inheritance_profile.to_dict(),
        })
        engine = PEGEngine(signal_profile=profile)
        text = (
            "Reference\n"
            "=========\n\n"
            "* import system\n"
            "* execution model\n"
        )
        hunks = list(engine.parse(text, "memory://reference/index.txt"))
        item_hunks = [h for h in hunks if h.node_kind == "md_list_item"]
        self.assertEqual(len(item_hunks), 2)
        self.assertEqual(item_hunks[0].list_role, "unordered_item")
        self.assertTrue(item_hunks[0].structural_path.endswith("/li_1"))

    def test_default_profile_keeps_lists_as_md_list(self):
        engine = PEGEngine(signal_profile=SplitterSignalProfile.default())
        text = (
            "Reference\n"
            "=========\n\n"
            "* import system\n"
            "* execution model\n"
        )
        hunks = list(engine.parse(text, "memory://reference/index.txt"))
        self.assertEqual([h.node_kind for h in hunks], ["md_heading", "md_list"])

    def test_list_items_infer_section_like_reference_targets(self):
        profile = SplitterSignalProfile.from_dict({
            "structured_text_profile": SplitterSignalProfile.default().structured_text_profile.to_dict(),
            "reference_extraction_profile": SplitterSignalProfile.default().reference_extraction_profile.to_dict(),
            "list_representation_profile": {
                "emit_list_items": True,
                "max_list_item_length": 320,
                "preserve_markers": True,
                "inherit_heading_ancestry": True,
            },
            "fragment_inheritance_profile": SplitterSignalProfile.default().fragment_inheritance_profile.to_dict(),
        })
        engine = PEGEngine(signal_profile=profile)
        text = (
            "Reference\n"
            "=========\n\n"
            "* 2. Lexical analysis\n"
            "  * 2.1. Line structure\n"
        )
        hunks = list(engine.parse(text, "memory://reference/index.txt"))
        item_hunks = [h for h in hunks if h.node_kind == "md_list_item"]
        self.assertEqual(item_hunks[0].normalized_cross_refs, ["lexical_analysis"])
        self.assertEqual(item_hunks[0].reference_kinds, ["list_section_title"])
        self.assertEqual(item_hunks[1].normalized_cross_refs, ["line_structure"])

    def test_fragments_inherit_reference_context_according_to_profile(self):
        parent = HyperHunk(
            content="alpha beta gamma delta epsilon zeta eta theta iota kappa",
            origin_id="memory://parent.txt",
            layer_type="CST",
            node_kind="md_paragraph",
            structural_path="doc/h1_parent/p1",
            cross_refs=["reference/import"],
            normalized_cross_refs=["reference/import"],
            reference_kinds=["rst_doc"],
            reference_confidence=0.95,
            import_context=["importlib"],
            token_count=10,
        )
        profile = SplitterSignalProfile.from_dict({
            "structured_text_profile": SplitterSignalProfile.default().structured_text_profile.to_dict(),
            "reference_extraction_profile": SplitterSignalProfile.default().reference_extraction_profile.to_dict(),
            "list_representation_profile": SplitterSignalProfile.default().list_representation_profile.to_dict(),
            "fragment_inheritance_profile": {
                "inherit_full_reference_context": False,
                "keep_parent_node_kind_family": True,
                "context_window_retain_ratio": 0.5,
            },
        })
        negotiator = Negotiator(max_tokens=2, overlap_ratio=0.5, signal_profile=profile)
        fragments = list(negotiator.negotiate(parent, prev_content="prefix words for context"))
        self.assertGreater(len(fragments), 1)
        self.assertEqual(fragments[0].cross_refs, [])
        self.assertEqual(fragments[0].normalized_cross_refs, [])
        self.assertEqual(fragments[0].reference_confidence, 0.0)
        self.assertIn("source_node_kind_family", fragments[0].metadata)
        self.assertLessEqual(len(fragments[0].context_window), len("words for context"))


if __name__ == "__main__":
    unittest.main()
