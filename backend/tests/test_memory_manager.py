import pytest
from unittest.mock import Mock
from agent.memory_manager import MemoryManager
from app_setup import DB_CONNECTION


@pytest.fixture
def setup(mocker):
    mocker.patch(
        "openai.ChatCompletion.create",
        return_value={"choices": [{"message": {"content": "summary"}}]},
    )
    memory_manager = MemoryManager(
        model="gpt-3.5-turbo-0613",
        table_name="test",
        db_connection=DB_CONNECTION,
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

    # def test_add_message(self):
    #     role = "user"
    #     content = "What's the weather like in Boston?"
    #     self.memory_manager.add_message(role, content)
    #     messages = self.memory_manager.get_messages()
    #     assert messages[0]["role"] == role
    #     assert messages[0]["content"] == content

    def test_get_total_tokens(self):
        tokens = self.memory_manager.get_total_tokens()
        assert isinstance(tokens, int)

    def test_get_messages(self):
        messages = self.memory_manager.get_messages()
        assert isinstance(messages, list)

    # def test_summarize(self):
    #     message = "This is a test message."
    #     summary, tokens = self.memory_manager.summarize(message)
    #     assert isinstance(summary, str)
    #     assert isinstance(tokens, int)

    # def test_set_system(self):
    #     input = {
    #         "system": "You are an AI Pair Programmer and a world class python developer helping the Human work on a project."
    #     }
    #     self.memory_manager.set_system(input)
    #     messages = self.memory_manager.get_messages()
    #     assert messages[0]["role"] == "system"
    #     assert messages[0]["content"] == input["system"]
