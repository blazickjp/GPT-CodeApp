import unittest
from backend.memory.system_prompt_handler import SystemPromptHandler

class TestSystemPromptHandler(unittest.TestCase):
    def setUp(self):
        self.handler = SystemPromptHandler(db_connection=None)

    def test_gen_rewrite_prompt(self):
        prompt = self.handler.gen_rewrite_prompt()
        self.assertIsInstance(prompt, str)
        self.assertIn("Rewrite the following prompt", prompt)
        self.assertIn("<tree>", prompt)
        self.assertIn("</tree>", prompt)