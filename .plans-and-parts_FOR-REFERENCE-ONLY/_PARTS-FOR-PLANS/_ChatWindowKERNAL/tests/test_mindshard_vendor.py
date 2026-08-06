from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.runtime.vendors.mindshard import ensure_bootstrap


class MindshardVendorTests(unittest.TestCase):
    def test_vendored_runtime_supports_chat_loop_and_evidence_pipeline(self) -> None:
        ensure_bootstrap()
        from agent.loops import get_loop
        from agent.shell import MindShardAgent
        from bridge.llm import EchoBridge

        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "agent_memory.db"
            agent = MindShardAgent.create(
                llm=EchoBridge(),
                db_path=str(db_path),
                loop=get_loop("plan_act_observe"),
            )
            try:
                chat_output = agent.chat("Remember that the parser uses staged passes.")
                run_result = agent.run("Summarize what we know about the parser.")
                recall = agent.memory.reflect("parser", budget=4)
                extracted = agent.memory.kernel.extract_evidence("parser", max_items=4)
                interrogated = agent.memory.kernel.interrogate(extracted.items, "parser")

                runtime = agent.memory.kernel.evidence_runtime
                self.assertIsNotNone(runtime)
                runtime.ingest_node(
                    kind="knowledge",
                    content="The parser keeps a staged pass list for syntax and validation.",
                    tags=["parser", "staged"],
                )
                assembled = agent.memory.kernel.assemble_bag("parser staged passes")

                self.assertTrue(chat_output)
                self.assertTrue(run_result.final_output)
                self.assertGreaterEqual(len(run_result.trace), 1)
                self.assertGreaterEqual(len(recall.memories), 1)
                self.assertGreaterEqual(len(extracted.items), 1)
                self.assertTrue(interrogated)
                self.assertGreaterEqual(len(assembled.items), 1)
            finally:
                agent.close()
