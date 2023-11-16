import json
from agent.coding_agent import CodingAgent
from memory.memory_manager import MemoryManager
from database.my_codebase import MyCodebase
from app_setup import setup_app


def main():
    # Set up the application
    AGENT, CODEBASE = setup_app()

    # Initialize the CodingAgent
    agent = CodingAgent(memory_manager=AGENT.memory_manager, codebase=CODEBASE)

    # Load configurations from the app into the agent
    agent.GPT_MODEL = "gpt-3.5-turbo"  # Or any specific model name you are using
    agent.memory_manager.max_tokens = 2048  # Set the max tokens for message history

    # CLI Interaction Loop
    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            print("Exiting the Coding Agent.")
            break

        try:
            # Prepare the data for the agent query
            data = {
                "model": agent.GPT_MODEL,
                "messages": [
                    {"role": "system", "content": ""},
                    {"role": "user", "content": user_input},
                ],
                "max_tokens": agent.memory_manager.max_tokens,
                "temperature": 0.7,  # Set a default temperature
            }

            # Use the message_streaming method to get a response from the agent
            responses = agent.message_streaming(data)
            for response in responses:
                print(f"Agent: {response}")

        except Exception as e:
            print(f"An error occurred: {e}")


# Entry point for the script
if __name__ == "__main__":
    main()
