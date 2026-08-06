import sys
import unittest
from pathlib import Path


EMITTER_SRC = Path(__file__).resolve().parents[1] / "src"
if str(EMITTER_SRC) not in sys.path:
    sys.path.insert(0, str(EMITTER_SRC))

from core.contract.hyperhunk import HyperHunk
from core.nucleus.bootstrap import BootstrapConfig, BootstrapNucleus


def _make_hunk(
    *,
    content: str,
    node_kind: str,
    structural_path: str,
    heading_trail=None,
    token_count: int = 20,
    embedding=None,
    origin_id: str = "memory://test",
    cross_refs=None,
):
    hunk = HyperHunk(
        content=content,
        origin_id=origin_id,
        layer_type="CST",
        node_kind=node_kind,
        structural_path=structural_path,
        heading_trail=list(heading_trail or []),
        cross_refs=list(cross_refs or []),
        token_count=token_count,
    )
    hunk.embedding = embedding
    return hunk


class BootstrapConfigTests(unittest.TestCase):
    def test_default_config_round_trip(self):
        config = BootstrapConfig.default()
        clone = BootstrapConfig.from_dict(config.to_dict())
        self.assertEqual(config.to_dict(), clone.to_dict())

    def test_missing_required_keys_rejected(self):
        payload = BootstrapConfig.default().to_dict()
        del payload["surface_fractions"]
        with self.assertRaises(ValueError):
            BootstrapConfig.from_dict(payload)

    def test_negative_values_rejected(self):
        payload = BootstrapConfig.default().to_dict()
        payload["edge_threshold"] = -0.1
        with self.assertRaises(ValueError):
            BootstrapConfig.from_dict(payload)

    def test_invalid_threshold_scale_rejected(self):
        payload = BootstrapConfig.default().to_dict()
        payload["semantic_absent_threshold_scale"] = 0.0
        with self.assertRaises(ValueError):
            BootstrapConfig.from_dict(payload)

    def test_invalid_explicit_reference_profile_rejected(self):
        payload = BootstrapConfig.default().to_dict()
        payload["explicit_reference_profile"]["target_hint_bonus"] = -0.1
        with self.assertRaises(ValueError):
            BootstrapConfig.from_dict(payload)

    def test_surface_fractions_must_sum_to_one(self):
        payload = BootstrapConfig.default().to_dict()
        payload["surface_fractions"]["grammatical"] = 0.99
        with self.assertRaises(ValueError):
            BootstrapConfig.from_dict(payload)

    def test_default_config_preserves_current_behavior_after_reload(self):
        a = _make_hunk(
            content="Paragraph about imports and modules.",
            node_kind="md_paragraph",
            structural_path="doc/h1_intro/p1",
            heading_trail=["Intro"],
            token_count=24,
        )
        b = _make_hunk(
            content="Another paragraph about modules and imports.",
            node_kind="md_paragraph",
            structural_path="doc/h1_intro/p2",
            heading_trail=["Intro"],
            token_count=26,
        )
        default_nucleus = BootstrapNucleus()
        round_trip_nucleus = BootstrapNucleus(
            config=BootstrapConfig.from_dict(BootstrapConfig.default().to_dict())
        )
        self.assertEqual(
            default_nucleus.evaluate(a, b).__dict__,
            round_trip_nucleus.evaluate(a, b).__dict__,
        )


class BootstrapBehaviorTests(unittest.TestCase):
    def test_code_exact_match_beats_generic_prose_exact_match(self):
        nucleus = BootstrapNucleus()

        code_a = _make_hunk(
            content="def add(x, y): return x + y",
            node_kind="function_definition",
            structural_path="module/add",
        )
        code_b = _make_hunk(
            content="def sub(x, y): return x - y",
            node_kind="function_definition",
            structural_path="module/sub",
        )
        prose_a = _make_hunk(
            content="This paragraph explains the module.",
            node_kind="md_paragraph",
            structural_path="doc/h1_intro/p1",
            heading_trail=["Intro"],
        )
        prose_b = _make_hunk(
            content="This paragraph also explains the module.",
            node_kind="md_paragraph",
            structural_path="doc/h1_intro/p2",
            heading_trail=["Intro"],
        )

        code_score = nucleus.evaluate(code_a, code_b).interaction_vector[0]
        prose_score = nucleus.evaluate(prose_a, prose_b).interaction_vector[0]
        self.assertGreater(code_score, prose_score)

    def test_heading_exact_match_beats_generic_paragraph_exact_match(self):
        nucleus = BootstrapNucleus()
        heading_a = _make_hunk(
            content="4. Execution model",
            node_kind="md_heading",
            structural_path="doc/h1_execution_model",
            heading_trail=["Execution model"],
        )
        heading_b = _make_hunk(
            content="6. Expressions",
            node_kind="md_heading",
            structural_path="doc/h1_expressions",
            heading_trail=["Expressions"],
        )
        paragraph_a = _make_hunk(
            content="Paragraph one",
            node_kind="md_paragraph",
            structural_path="doc/h1_intro/p1",
            heading_trail=["Intro"],
        )
        paragraph_b = _make_hunk(
            content="Paragraph two",
            node_kind="md_paragraph",
            structural_path="doc/h1_intro/p2",
            heading_trail=["Intro"],
        )

        heading_score = nucleus.evaluate(heading_a, heading_b).interaction_vector[0]
        paragraph_score = nucleus.evaluate(paragraph_a, paragraph_b).interaction_vector[0]
        self.assertGreater(heading_score, paragraph_score)

    def test_fragment_similarity_stays_weak(self):
        nucleus = BootstrapNucleus()
        frag_a = _make_hunk(
            content="fragment alpha",
            node_kind="fragment_of_md_paragraph",
            structural_path="doc/h1_intro/frag1",
            token_count=8,
        )
        frag_b = _make_hunk(
            content="fragment beta",
            node_kind="fragment_of_md_paragraph",
            structural_path="doc/h1_intro/frag2",
            token_count=8,
        )

        frag_score = nucleus.evaluate(frag_a, frag_b).interaction_vector[0]
        self.assertLessEqual(frag_score, 0.12)

    def test_semantic_absent_threshold_scale_changes_only_threshold_decision(self):
        base = BootstrapConfig.default().with_overrides({
            "edge_threshold": 0.34,
            "semantic_absent_threshold_scale": 0.8,
        })
        scaled_nucleus = BootstrapNucleus(config=base)
        default_nucleus = BootstrapNucleus(
            config=BootstrapConfig.default().with_overrides({"edge_threshold": 0.34})
        )

        a = _make_hunk(
            content="Paragraph about imports.",
            node_kind="md_paragraph",
            structural_path="doc/h1_intro/p1",
            heading_trail=["Intro"],
            token_count=20,
        )
        b = _make_hunk(
            content="Paragraph about modules.",
            node_kind="md_paragraph",
            structural_path="doc/h1_intro/p2",
            heading_trail=["Intro"],
            token_count=22,
        )

        default_result = default_nucleus.evaluate(a, b)
        scaled_result = scaled_nucleus.evaluate(a, b)

        self.assertEqual(default_result.connection_strength, scaled_result.connection_strength)
        self.assertEqual(default_result.routing_profile, scaled_result.routing_profile)
        self.assertEqual(default_result.interaction_type, scaled_result.interaction_type)
        self.assertEqual(default_result.interaction_vector, scaled_result.interaction_vector)
        self.assertNotEqual(default_result.above_threshold, scaled_result.above_threshold)

    def test_explicit_cross_ref_boost_improves_structural_signal(self):
        baseline = BootstrapNucleus()
        tuned = BootstrapNucleus(
            config=BootstrapConfig.default().with_overrides({
                "explicit_reference_profile": {
                    "overlap_weight": 0.0,
                    "target_hint_bonus": 0.2,
                }
            })
        )

        a = _make_hunk(
            content="See the import system details.",
            node_kind="md_paragraph",
            origin_id="memory://import",
            structural_path="doc/h1_import/p1",
            heading_trail=["Import System"],
            cross_refs=["import.txt"],
        )
        b = _make_hunk(
            content="Import machinery reference.",
            node_kind="md_heading",
            origin_id="C:/docs/reference/import.txt",
            structural_path="doc/h1_import_system",
            heading_trail=["Import System"],
        )

        baseline_structural = baseline.evaluate(a, b).interaction_vector[1]
        tuned_structural = tuned.evaluate(a, b).interaction_vector[1]
        self.assertGreater(tuned_structural, baseline_structural)


if __name__ == "__main__":
    unittest.main()
