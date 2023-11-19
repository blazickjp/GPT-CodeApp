import unittest
import instructor
import difflib
from openai import OpenAI
from unittest.mock import MagicMock, mock_open, patch, call
from agent.coding_agent import CodingAgent
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
        # Mock the CodingAgent and its dependencies
        self.agent = CodingAgent(memory_manager=None, function_map=None, codebase=None)
        self.agent.ops_to_execute = [add_function_op, delete_function_op]
        # Patch the open function in the coding_agent module
        self.mock_open = mock_open(read_data=ORIGINAL_CODE)
        self.open_patch = patch("agent.coding_agent.open", self.mock_open)
        self.open_patch.start()

    def tearDown(self):
        self.open_patch.stop()

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
