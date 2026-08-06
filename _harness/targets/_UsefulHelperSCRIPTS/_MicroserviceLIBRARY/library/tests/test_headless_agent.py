import sqlite3
import tempfile
import unittest
from pathlib import Path

from library.headless_agent import SQLiteSessionAgent


class HeadlessAgentTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.temp_root = Path(self._tmp.name)
        self.db_path = self.temp_root / 'agent.db'
        self.agent = SQLiteSessionAgent(self.db_path, window_limit=3, token_budget=120)
        self.session_id = self.agent.create_session(model='llama3.2:3b', config={'window_limit': 3})

    def tearDown(self):
        self._tmp.cleanup()

    def test_schema_uses_manifest_table_names(self):
        conn = sqlite3.connect(self.db_path)
        try:
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            conn.close()
        self.assertIn('agent_sessions', tables)
        self.assertIn('agent_memory', tables)
        self.assertIn('agent_knowledge', tables)

    def test_context_is_pinned_plus_recent_unpinned(self):
        self.agent.append_memory(session_id=self.session_id, role='system', content='System rules.', is_pinned=True)
        for idx in range(5):
            self.agent.append_memory(session_id=self.session_id, role='user' if idx % 2 == 0 else 'assistant', content=f'Turn {idx} about the basement key.')

        context = self.agent.get_full_context(self.session_id, window_limit=3)
        self.assertEqual(len(context), 4)
        self.assertTrue(context[0]['is_pinned'])
        self.assertEqual([item['content'] for item in context[1:]], [
            'Turn 2 about the basement key.',
            'Turn 3 about the basement key.',
            'Turn 4 about the basement key.',
        ])

    def test_count_and_evict_oldest_memories(self):
        for idx in range(5):
            self.agent.append_memory(session_id=self.session_id, role='user', content=f'Question {idx} about the attic switch.')

        token_count = self.agent.count_window_tokens(self.session_id, window_limit=3)
        self.assertGreater(token_count, 0)
        evicted = self.agent.evict_oldest_memories(self.session_id, keep_recent=2)
        self.assertEqual(len(evicted), 3)
        self.assertTrue(all(item['metadata'].get('eviction_reason') == 'window_overflow' for item in evicted))

    def test_summarize_and_pin_evicted_creates_summary_memory(self):
        for idx in range(4):
            self.agent.append_memory(session_id=self.session_id, role='user', content=f'Observation {idx} about the radio room.')

        summary_id = self.agent.summarize_and_pin_evicted(self.session_id, keep_recent=2)
        self.assertIsNotNone(summary_id)
        context = self.agent.get_full_context(self.session_id, window_limit=2)
        summaries = [item for item in context if item['role'] == 'summary']
        self.assertEqual(len(summaries), 1)
        self.assertTrue(summaries[0]['is_pinned'])

    def test_store_and_search_knowledge(self):
        self.agent.store_knowledge(
            source='world',
            category='observation',
            content='The library desk contains a brass key and a folded map.',
            metadata={'cell_id': 'library'},
        )
        self.agent.store_knowledge(
            source='human_told_me',
            category='quest',
            content='The cellar door only opens after the generator is powered.',
        )

        hits = self.agent.search_knowledge('Where is the brass key?', limit=3)
        self.assertTrue(hits)
        self.assertEqual(hits[0]['source'], 'world')

        quest_hits = self.agent.search_knowledge('generator powered', category='quest', limit=3)
        self.assertEqual(len(quest_hits), 1)
        self.assertEqual(quest_hits[0]['category'], 'quest')

    def test_build_context_reinjects_evicted_memory_and_knowledge(self):
        self.agent.append_memory(session_id=self.session_id, role='system', content='Stay in character.', is_pinned=True)
        for text in [
            'The human mentioned the cellar key once already.',
            'We found a clue about the generator room.',
            'Current turn about the upstairs hall.',
            'Latest note about the cellar key location.',
        ]:
            self.agent.append_memory(session_id=self.session_id, role='user', content=text)

        self.agent.store_knowledge(
            source='observation',
            category='observation',
            content='A note in the study says the cellar key hangs behind the clock.',
        )

        bundle = self.agent.build_context(
            self.session_id,
            'How do we get the cellar key?',
            system_prompt='Be concise.',
            knowledge_limit=2,
            evicted_limit=2,
            window_limit=2,
        )

        self.assertEqual(bundle['model_messages'][0]['content'], 'Be concise.')
        self.assertTrue(any(item['role'] == 'system' and 'Retrieved knowledge' in item['content'] for item in bundle['model_messages']))
        self.assertTrue(any(item['role'] == 'system' and 'Relevant evicted session memory' in item['content'] for item in bundle['model_messages']))
        self.assertEqual(bundle['model_messages'][-1]['content'], 'How do we get the cellar key?')


if __name__ == '__main__':
    unittest.main()
