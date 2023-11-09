import unittest
from unittest.mock import patch, MagicMock
from agent.agent import CodingAgent
from memory.memory_manager import MemoryManager
from database.my_codebase import MyCodebase

IGNORE_DIRS = ["node_modules", ".next", ".venv", "__pycache__", ".git"]
FILE_EXTENSIONS = [".js", ".py", ".md"]


class TestCodingAgent(unittest.TestCase):
    def setUp(self):
        # Mock database connection setup
        self.mock_db_connection = MagicMock()
        self.memory_manager = MemoryManager(db_connection=self.mock_db_connection)
        self.codebase = MyCodebase(
            db_connection=self.mock_db_connection,
        )

        # Initialize the agent for testing
        self.agent = CodingAgent(
            memory_manager=self.memory_manager, codebase=self.codebase
        )
        self.agent.register_ast_functions()  # Register AST functions

    def test_apply_ast_changes(self):
        # Mock the ASTChangeApplicator to avoid actual changes
        with patch("agent.agent.ASTChangeApplicator") as MockASTChangeApplicator:
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

    # Additional tests could include:
    # - Testing message history retrieval and addition
    # - Testing specific agent queries and responses
    # - Testing error handling and edge cases


if __name__ == "__main__":
    unittest.main()
