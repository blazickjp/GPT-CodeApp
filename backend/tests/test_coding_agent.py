import unittest
import instructor
import difflib
from openai import OpenAI
from unittest.mock import MagicMock, mock_open, patch, call
from agent.coding_agent import CodingAgent, QueryRewrite
from memory.memory_manager import MemoryManager
from database.my_codebase import MyCodebase
from agent.agent_functions.file_ops import _OP_LIST, AddFunction, DeleteFunction


client = instructor.patch(OpenAI())

IGNORE_DIRS = ["node_modules", ".next", ".venv", "__pycache__", ".git"]
FILE_EXTENSIONS = [".js", ".py", ".md"]

# Sample code for testing purposes
ORIGINAL_CODE = "def example():\n    pass\n"
MODIFIED_CODE_ADD = (
    "def example():\n    pass\n\ndef added_function():\n    return 'test'\n"
)
MODIFIED_CODE_DELETE = ""

# Sample operation instances for testing
add_function_op = AddFunction(
    file_name="example.py",
    function_name="added_function",
    args="",
    body="return 'test'",
    decorator_list=[],
)
delete_function_op = DeleteFunction(file_name="example.py", function_name="example")


class TestCodingAgent(unittest.TestCase):
    def setUp(self):
        self.agent = CodingAgent(memory_manager=None)

    def test_query_rewrite(self):
        # Test basic rewrite
        rewrite = QueryRewrite(rewritten_query="test query")
        self.assertEqual(rewrite.rewritten_query, "test query")
        self.assertEqual(rewrite.to_dict(), {"rewritten_query": "test query"})
        
        # Test empty query
        empty_rewrite = QueryRewrite(rewritten_query="")
        self.assertEqual(empty_rewrite.rewritten_query, "")
        
    def test_rewrite_input(self):
        """Test the rewrite_input method of the CodingAgent."""
        # Test basic rewrite
        original_query = "original query"
        rewritten_query = self.agent.rewrite_input(original_query)
        self.assertIsInstance(rewritten_query, str)
        self.assertNotEqual(rewritten_query, original_query)
        self.assertIn("rewritten", rewritten_query)

        # Test empty query
        empty_query = ""
        rewritten_empty = self.agent.rewrite_input(empty_query)
        self.assertEqual(rewritten_empty, "")

        # Test long query
        long_query = "a" * 1000
        rewritten_long = self.agent.rewrite_input(long_query)
        self.assertIsInstance(rewritten_long, str)
        self.assertNotEqual(rewritten_long, long_query)

    def test_execute_ops(self):
        # Call the method to test
        diffs = self.agent.execute_ops(self.agent.ops_to_execute)
        print("Diff: ", diffs)

        # We expect two diffs: one for the addition and one for the deletion
        expected_diffs = [
            "--- before.py\n+++ after.py\n@@ -1,2 +1,6 @@\n def example():\n     pass\n+\n+\n+def added_function():\n+    return 'test'\n",
            "--- before.py\n+++ after.py\n@@ -1,2 +0,0 @@\n-def example():\n-    pass\n",
        ]

        # Check that the diffs match what we expect
        self.assertEqual(diffs, expected_diffs)


class TestCodingAgent1(unittest.TestCase):
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
