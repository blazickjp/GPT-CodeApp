import unittest
from unittest.mock import patch, MagicMock
from agent.coding_agent import CodingAgent
from memory.memory_manager import MemoryManager
from database.my_codebase import MyCodebase
from agent.agent_functions.changes import Changes
from agent.coding_agent import FunctionCall

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
            functions=[Changes],
            callables=[Changes],
        )
        self.agent.register_ast_functions()  # Register AST functions

    def test_register_ast_functions(self):
        self.agent.register_ast_functions()
        self.assertIn("apply_ast_changes", self.agent.function_map)

    def test_apply_ast_changes1(self):
        with patch("agent.coding_agent.ASTChangeApplicator") as MockASTChangeApplicator:
            mock_applicator = MockASTChangeApplicator.return_value
            mock_applicator.apply_changes.return_value = "new source code"
            result = self.agent.apply_ast_changes("source code", "changes")
            self.assertEqual(result, "new source code")

    def test_handle_ast_change_command(self):
        with patch("agent.coding_agent.ASTChangeApplicator") as MockASTChangeApplicator:
            mock_applicator = MockASTChangeApplicator.return_value
            mock_applicator.apply_changes.return_value = "new source code"
            result = self.agent.handle_ast_change_command(
                {"source_code": "source code", "changes": "changes"}
            )
            self.assertEqual(result, "new source code")

    def test_should_stop_and_has_function(self):
        # Mock the delta to simulate the response choices structure
        self.agent.function_to_call = FunctionCall(name="test")

        class MockChoice:
            def __init__(self, finish_reason):
                self.finish_reason = finish_reason

        class MockResponse:
            def __init__(self, choices):
                self.choices = [MockChoice(finish_reason="stop")]

        delta = MockResponse(choices=[MockChoice(finish_reason="stop")])
        print(delta)
        result = self.agent.should_stop_and_has_function(delta)
        self.assertTrue(result)

    def test_process_function_call(self):
        self.agent.function_to_call = FunctionCall(name="test")

        class MockChoice:
            def __init__(self, finish_reason):
                self.finish_reason = finish_reason

        class MockResponse:
            def __init__(self, choices):
                self.choices = [MockChoice(finish_reason=choices)]
                self.function_call = FunctionCall(name="test", arguments="arguments")

        delta = MockResponse(choices=[MockChoice(finish_reason="stop")])
        result = list(self.agent.process_function_call(delta, 0))
        self.assertEqual(result, ["arguments"])

    def test_execute_function(self):
        self.agent.function_map = {"name": MagicMock()}
        self.agent.function_to_call = FunctionCall(name="name", arguments="arguments")
        self.agent.function_to_call.arguments = "{}"
        result = list(self.agent.execute_function())
        self.assertEqual(result, [])

    def test_process_json(self):
        result = self.agent.process_json('{"key": "value"}')
        self.assertEqual(result, {"key": "value"})

    def test_agent_query(self):
        self.agent.query = MagicMock()
        self.agent.query.return_value = ["response"]
        result = list(self.agent.query("input"))
        self.assertEqual(result, ["response"])

    def test_apply_ast_changes(self):
        # Mock the ASTChangeApplicator to avoid actual changes
        with patch("agent.coding_agent.ASTChangeApplicator") as MockASTChangeApplicator:
            mock_applicator = MockASTChangeApplicator.return_value
            mock_applicator.apply_changes.return_value = "print('Hello, World!')"

            # Define the source code and expected code after changes
            source_code = "print('Hello World')"
            changes = [
                # Define the changes in the format that your ASTChangeApplicator expects
            ]
            expected_code = "print('Hello, World!')"

            # Apply the changes using the agent's method
            updated_code = self.agent.apply_ast_changes(source_code, changes)

            # Assert that the updated_code matches the expected_code
            self.assertEqual(updated_code, expected_code)
            mock_applicator.apply_changes.assert_called_once_with(changes)


if __name__ == "__main__":
    unittest.main()
