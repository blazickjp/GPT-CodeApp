import pytest
from unittest.mock import Mock
from agent.memory_manager import MemoryManager


@pytest.fixture
def setup():
    # Create a mock connection object
    conn = Mock()

    # Create a mock cursor object
    cursor = Mock()

    # Configure the mock connection to return the mock cursor when cursor() is called
    conn.cursor.return_value = cursor

    # Create an instance of MemoryManager with the mock connection
    memory_manager = MemoryManager(
        model="gpt-3.5-turbo-0613",
        table_name="test",
        db_connection=conn,
    )
    return memory_manager


class TestMemoryManager:
    @pytest.fixture(autouse=True)
    def setup_method(self, setup):
        self.memory_manager = setup

    def test_get_total_tokens_in_message(self):
        message = "This is a test message."
        tokens = self.memory_manager.get_total_tokens_in_message(message)
        print(f"TOKENS: {tokens}")
        assert isinstance(tokens, int)

    def test_get_total_tokens(self):
        tokens = self.memory_manager.get_total_tokens()
        assert (
            tokens >= 0
        ), f"Expected tokens to be greater than or equal to 0, but got {tokens}"
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
        self.memory_manager.set_system(input)
        self.memory_manager.cur.execute.assert_called()  # Check if execute was called on cursor

    def test_add_message(self):
        self.memory_manager.add_message("test_role", "test_content")
        self.memory_manager.cur.execute.assert_called()
        self.memory_manager.conn.commit.assert_called()
        call_args = self.memory_manager.cur.execute.call_args
        sql_query, params = call_args[0]
        assert type(params[0]) == str
        assert params[1] == "test_role"
        assert params[2] == "test_content"
        assert (
            params[3] > 0
        ), f"Expected tokens to be greater than 0, but got {params[3]}"
        assert params[4] is None
        assert params[5] is None
        assert params[6] is not None
