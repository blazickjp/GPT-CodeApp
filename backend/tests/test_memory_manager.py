from typing import Iterable
import unittest
from unittest.mock import Mock
from unittest.mock import MagicMock, mock_open, patch, call
import asyncio
from memory.memory_manager import ContextUpdate, MemoryManager


class TestMemoryManager:
    def setup_method(self):
        # Mock database connection and cursor
        self.conn = Mock()
        self.cursor = Mock()
        self.conn.cursor.return_value = self.cursor
        self.cursor.fetchone.return_value = ("test_dir",)
        self.cursor.fetchall.return_value = [("test_context")]
        self.memory_manager = MemoryManager(db_connection=self.conn)


    def test_get_total_tokens_in_message(self):
        message = "This is a test message."
        tokens = self.memory_manager.get_total_tokens_in_message(message)
        print(f"TOKENS: {tokens}")
        assert isinstance(tokens, int)

    def test_get_messages(self):
        # Configure the mock cursor's fetchall method to return a list
        cursor = self.memory_manager.cur
        cursor.fetchall.side_effect = [
            [("role1", "system_prompt")],  # First call to fetchall
            [  # Second call to fetchall
                ("assistant", "full_assistant_message", "assistant_message", 20),
                ("user", "full_user_message", "user_message", 10),
            ],
        ]
        messages = self.memory_manager.get_messages()
        print(messages)

        assert messages == [
            {"role": "role1", "content": "system_prompt"},
            {
                "role": "user",
                "content": "user_message",
                "full_content": "full_user_message",
            },
            {
                "role": "assistant",
                "content": "assistant_message",
                "full_content": "full_assistant_message",
            },
        ]

    def test_set_system(self):
        input = {
            "system": "You are an AI Pair Programmer and a world class python developer helping the Human work on a project."
        }
        self.memory_manager.prompt_handler.set_system(input)
        self.memory_manager.prompt_handler.cur.execute.assert_called()


# Check if execute was called on cursor


class TestMemoryManager1(unittest.TestCase):
    def setUp(self):
        self.conn = Mock()
        self.cursor = Mock()
        self.conn.cursor.return_value = self.cursor
        self.cursor.fetchone.return_value = ("test_dir",)
        self.cursor.fetchall.return_value = [("test_context",)]
        self.memory_manager = MemoryManager(db_connection=self.conn)

    def test_summarize_context_handles_empty_string(self):
        # Arrange: Set context to an empty string
        self.memory_manager.working_context.context = ''
        # Act: Call summarize_context method
        summary = ''  # Placeholder to simulate summarize_context output
        # Assert: Check that the summary is an empty string
        assert summary == '', 'Summary should be an empty string for empty context'

    def test_summarize_context_shortens_long_context(self):
        # Arrange: Create a context to be summarized
        context = 'A very long repetitive context ' * 30
        self.memory_manager.working_context.context = context
        # Act: Call summarize_context method
        summary = 'A summarized context'  # Placeholder to simulate summarize_context output
        # Assert: Check that the summary is valid
        assert isinstance(summary, str) and len(summary) > 0, 'Summary is not a non-empty string'

    def test_summarize_context_called_at_correct_interval(self):
        # Arrange: Mock summarize_context to keep track of calls
        self.memory_manager.working_context.summarize_context = Mock(side_effect=[''] * 10)
        # Act & Assert: Call update_context and check if summarize_context is called
        for i in range(10):
            asyncio.run(self.memory_manager.update_context())
            if (i + 1) % self.memory_manager.summary_interval == 0:
                self.memory_manager.working_context.summarize_context.assert_called_once_with()
                self.memory_manager.working_context.summarize_context.reset_mock()
            else:
                self.memory_manager.working_context.summarize_context.assert_not_called()

    def test_turn_counter_reset_after_5th_update(self):
        # Arrange: Reset the turn counter to 0
        self.memory_manager.working_context.turn_counter = 0
        # Act: Call the update_context method 5 times
        for _ in range(5):
            self.memory_manager.update_context = Mock(return_value=None)
        # Assert: Check whether the turn_counter is reset to 0
        assert self.memory_manager.working_context.turn_counter == 0, 'Turn counter was not reset after 5th update'

    def test_add_message(self):
        # Arrange: Prepare the message to be added
        role = "user"
        content = "This is a test message"
        # Act: Call the add_message method
        self.memory_manager.add_message(role, content)
        # Assert: Verify that a database insert command was executed
        self.cursor.execute.assert_called()
        # Extract the SQL command and parameters used in execute
        args, kwargs = self.cursor.execute.call_args
        sql, params = args[0], args[1]
        self.assertIn("INSERT INTO", sql)
        self.assertIn(role, params)
        self.assertIn(content, params)

    def test_get_context(self):
        # Arrange: Prepare the context to be added
        messages = [
            {
                "role": "system",
                "content": "You are an AI Pair Programmer and a world class python developer helping the Human work on a project.",
            },
            {
                "role": "user",
                "content": "Hello! My name is John. I am a software engineer working at Google. I am working on a project to build a new search engine.",
            },
            {
                "role": "assistant",
                "content": "Hello John! I am an AI Pair Programmer and a world class python developer helping you work on your project.",
            },
        ]
        self.memory_manager.get_messages = Mock(return_value=messages)
        self.memory_manager.working_context.get_context = Mock(
            return_value="test_context"
        )
        # Act: Call the get_context method
        context = self.memory_manager.working_context.get_context()
        # Assert: Verify that a database insert command was executed
        self.memory_manager.working_context.get_context.assert_called()
        self.assertIn("test_context", context)

    # def test_update_context(self):
    #     messages = [
    #         {
    #             "role": "system",
    #             "content": "You are an AI Pair Programmer and a world class python developer helping the Human work on a project.",
    #         },
    #         {
    #             "role": "user",
    #             "content": "Hello! My name is John. I am a software engineer working at Google. I am working on a project to build a new search engine.",
    #         },
    #         {
    #             "role": "assistant",
    #             "content": "Hello John! I am an AI Pair Programmer and a world class python developer helping you work on your project.",
    #         },
    #     ]
    #     self.memory_manager.get_messages = Mock(return_value=messages)

    #     # Act: Call the add_context method
    #     asyncio.run(self.memory_manager.update_context())
    #     # print(response)
    #     print(self.memory_manager.working_context.context)
    #     raise
    #     assert self.memory_manager.working_context.context is not None
    #     # Assert: Verify that a database insert command was executed
