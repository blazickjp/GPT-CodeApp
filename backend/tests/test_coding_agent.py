import unittest
from unittest.mock import patch, MagicMock
from agent.coding_agent import CodingAgent
from memory.memory_manager import MemoryManager
from database.my_codebase import MyCodebase
from agent.agent_functions.changes import FunctionOperations

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
            # functions=[FunctionOperations],
            # callables=[FunctionOperations],
        )
        self.agent.register_ast_functions()  # Register AST functions

    def test_query_generates_valid_responses(self):
        # Setup: Provide a valid input string
        input_string = "Please write a Python function to add two numbers."

        # Mock the streaming response from the OpenAI API
        # Simulate streaming by returning a list of dictionaries representing response chunks
        mocked_streaming_response = [
            '{"choices": [{"finish_reason": null, "delta": {"content": "def add(a, b):"}}]}',
            '{"choices": [{"finish_reason": null, "delta": {"content": " return a + b"}}]}',
            '{"choices": [{"finish_reason": "stop", "delta": {}}]}',  # Indicate the end of the stream
        ]

        with patch(
            "openai.ChatCompletion.create", side_effect=mocked_streaming_response
        ):
            # Execution: Call the query method and iterate over the generator
            response_generator = self.agent.query(input_string)
            responses = [response for response in response_generator]

            # Assertion: Check if the responses are valid and as expected
            self.assertEqual(len(responses), 2)  # Check if two responses were generated
            self.assertIn(
                "Please write a Python function to add two numbers.", responses[0]
            )
            self.assertIn("def add(a, b): return a + b", responses[1])

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

    def test_process_function_call(self):
        delta = {"function_call": {"name": "name", "arguments": "arguments"}}
        result = list(self.agent.process_function_call(delta, 0))
        self.assertEqual(result, ["arguments"])

    def test_should_stop_and_has_function(self):
        delta = {"choices": [{"finish_reason": "stop"}]}
        self.agent.function_to_call.name = "name"
        result = self.agent.should_stop_and_has_function(delta)
        self.assertTrue(result)

    def test_execute_function(self):
        self.agent.function_map = {"name": MagicMock()}
        self.agent.function_to_call.name = "name"
        self.agent.function_to_call.arguments = "{}"
        result = list(self.agent.execute_function())
        self.assertEqual(result, [None])

    def test_process_json(self):
        result = self.agent.process_json('{"key": "value"}')
        self.assertEqual(result, {"key": "value"})

    def test_query(self):
        with patch("openai.ChatCompletion.create") as mock_create:
            mock_create.return_value = [
                {
                    "choices": [
                        {"finish_reason": "stop", "delta": {"content": "response"}}
                    ]
                }
            ]
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
