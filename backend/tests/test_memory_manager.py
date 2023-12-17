import unittest
from unittest.mock import Mock
import asyncio
from memory.memory_manager import ContextUpdate, MemoryManager


class TestMemoryManager:
    def setup_method(self):
        # Create a mock connection object
        conn = Mock()

        # Create a mock cursor object
        cursor = Mock()
        cursor.fetchone.return_value = ("some_value",)  # fetchone now returns a tuple

        conn.cursor.return_value = cursor

        # Create an instance of MemoryManager with the mock connection
        self.memory_manager = MemoryManager(
            model="gpt-3.5-turbo-16k",
            table_name="test",
            db_connection=conn,
        )

        return self.memory_manager

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
                ("user", "full_user_message", "user_message", 10),
                ("assistant", "full_assistant_message", "assistant_message", 20),
            ],
        ]

        assert self.memory_manager.get_messages() == [
            {"role": "role1", "content": "system_prompt"},
            {
                "role": "assistant",
                "content": "assistant_message",
                "full_content": "full_assistant_message",
            },
            {
                "role": "user",
                "content": "user_message",
                "full_content": "full_user_message",
            },
        ]

    def test_set_system(self):
        input = {
            "system": "You are an AI Pair Programmer and a world class python developer helping the Human work on a project."
        }
        self.memory_manager.prompt_handler.set_system(input)
        self.memory_manager.prompt_handler.cur.execute.assert_called()  # Check if execute was called on cursor


class TestMemoryManager1(unittest.TestCase):
    def setUp(self):
        # Mock database connection and cursor
        self.conn = Mock()
        self.cursor = Mock()
        self.conn.cursor.return_value = self.cursor
        # Set up __getitem__ to return a mock object with a specific return value
        self.cursor.fetchone.return_value = ("expected_directory",)
        # Initialize MemoryManager with the mock connection
        self.memory_manager = MemoryManager(db_connection=self.conn)

    def test_add_message(self):
        # Arrange: Prepare the message to be added
        role = "user"
        content = "This is a test message"
        # Act: Call the add_message method
        self.memory_manager.add_message(role, content)
        # Assert: Verify that a database insert command was executed
        self.cursor.execute.assert_called()
        # Optionally, check the arguments passed to the execute method
        args, kwargs = self.cursor.execute.call_args
        sql, params = args
        self.assertIn("INSERT INTO", sql)
        self.assertEqual(params[1], role)
        self.assertEqual(params[2], content)

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
        # Act: Call the add_context method
        response = asyncio.run(self.memory_manager.update_context())
        assert isinstance(response, ContextUpdate)
        assert response.new_context is not None
        # Assert: Verify that a database insert command was executed
