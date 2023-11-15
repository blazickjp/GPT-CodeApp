import unittest
import instructor
from openai import OpenAI
from unittest.mock import MagicMock
from agent.coding_agent import CodingAgent
from memory.memory_manager import MemoryManager
from database.my_codebase import MyCodebase
from agent.agent_functions.file_ops import _OP_LIST


client = instructor.patch(OpenAI())

IGNORE_DIRS = ["node_modules", ".next", ".venv", "__pycache__", ".git"]
FILE_EXTENSIONS = [".js", ".py", ".md"]


class TestCodingAgent(unittest.TestCase):
    def setUp(self):
        # Mock database connection setup
        self.mock_db_connection = MagicMock()
        self.memory_manager = MemoryManager(db_connection=self.mock_db_connection)
        self.codebase = MyCodebase(
            db_connection=self.mock_db_connection,
            file_extensions=FILE_EXTENSIONS,
            ignore_dirs=IGNORE_DIRS,
        )

        # Initialize the agent for testing
        self.agent = CodingAgent(
            memory_manager=self.memory_manager,
            codebase=self.codebase,
            function_map=[_OP_LIST],
        )

    def test_process_json(self):
        result = self.agent.process_json('{"key": "value"}')
        self.assertEqual(result, {"key": "value"})

    def test_agent_query(self):
        self.agent.query = MagicMock()
        self.agent.query.return_value = ["response"]
        result = list(self.agent.query("input"))
        self.assertEqual(result, ["response"])


if __name__ == "__main__":
    unittest.main()
