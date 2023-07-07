import openai
import json
import time
import psycopg2
from termcolor import colored
import tiktoken


class MemoryManager:
    """
    A memory manager for managing conversation history and archiving old conversation data.

    Attributes:
    ----------
    model : str
        The model being used for the conversation, such as "gpt-3.5-turbo-0613".

    max_tokens : int
        The maximum number of tokens that can be used in the conversation history.

    system : str
        The system message for the conversation.

    messages : list
        The list of messages in the conversation history. Each message is a dictionary with
        keys "role", "content", and "interaction_index".

    summary : str
        A summary of the conversation history.

    conn : psycopg2.extensions.connection
        The connection to the PostgreSQL database.

    cur : psycopg2.extensions.cursor
        The cursor for interacting with the PostgreSQL database.

    Methods:
    -------
    add_message(role, content, override_truncate=False):
        Adds a message to the conversation history.

    truncate_history():
        Truncates the conversation history to fit within the max_tokens limit.

    archive_memory_item(memory_item):
        Archives a memory item in the PostgreSQL database.

    summarize_history():
        Summarizes the conversation history and resets the messages to a system message with the summary.

    get_total_tokens_in_message(message):
        Returns the number of tokens in a message.

    get_total_tokens():
        Returns the total number of tokens in the conversation history.

    display_conversation(detailed=False):
        Prints the conversation history to the console.

    display_conversation_html(detailed=False):
        Returns the conversation history as an HTML string.

    load_memory():
        Loads memory items from the PostgreSQL database into the conversation history until the total number of tokens
        in the conversation history reaches the max_tokens limit.
    """

    def __init__(self, model="gpt-3.5-turbo", system=None, max_tokens=1000):
        self.model = model
        self.max_tokens = max_tokens
        self.system = "You are a helpful AI assistant." if not system else system
        self.messages = [
            {
                "role": "system",
                "content": self.system,
                "interaction_index": time.time() * 1000,
            }
        ]
        self.summary = ""
        # Connect to the PostgreSQL database
        self.conn = psycopg2.connect(
            host="localhost", database="memory", user="joe", password="1234"
        )

        # Create a cursor object
        self.cur = self.conn.cursor()
        self.create_tables()
        self.conn.commit()

    def add_message(self, role, content, override_truncate=False):
        timestamp = int(time.time() * 1000)  # Current timestamp in milliseconds
        self.messages.append(
            {"role": role, "content": content, "interaction_index": timestamp}
        )

        if not override_truncate and self.get_total_tokens() > self.max_tokens:
            self.truncate_history()

    def truncate_history(self):
        """Truncate the history to fit within the max_tokens limit."""
        print("Truncating history...")
        total_tokens = sum(len(item["content"]) for item in self.messages)
        while total_tokens > self.max_tokens // 2:
            # Check if the message to be removed is the first message and is a system message
            if len(self.messages) > 1:
                removed_item = self.messages.pop(
                    1
                )  # Pop the second message instead of the first
                total_tokens -= len(removed_item["content"])
                self.archive_memory_item(removed_item)
            else:
                # If there is only the system message, do nothing.
                break

    def archive_memory_item(self, memory_item):
        """Archive a memory item in the database."""
        print("Archiving memory item...")
        interaction_index = memory_item.get("interaction_index")
        if interaction_index is not None:
            interaction_index = int(interaction_index)  # Make sure it's an integer
        else:
            interaction_index = int(
                time.time() * 1000
            )  # Default to current timestamp in milliseconds

        # Check if the content is already a JSON string
        if isinstance(memory_item["content"], str):
            # If it's already a JSON string, escape single quotes
            memory_item_json = json.dumps(memory_item).replace("'", "''")
        else:
            # If it's a dictionary, convert it to a JSON string
            memory_item_json = json.dumps(memory_item)

        # Try to insert into the database
        query = "INSERT INTO memory (interaction_index, memory_item) VALUES (%s, %s)"
        while True:
            try:
                self.cur.execute(query, (interaction_index, memory_item_json))
                self.conn.commit()
                break
            except psycopg2.errors.UniqueViolation as e:
                print(e)
                # If interaction_index already exists, increment it, rollback the transaction and retry
                interaction_index += 1
                self.conn.rollback()

    def summarize_history(self):
        # Combine the content of all messages into a single string
        full_history = "\n".join(
            [
                f"{item['role'].capitalize()}: {item['content']}"
                for item in self.messages
            ]
        )

        # Use Chat API to summarize the history
        prompt = f"User: Please summarize the following conversation: \n{full_history}\n\nAssistant:"
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,  # You can adjust this value
        )

        summary = response["choices"][0]["message"]["content"].strip()
        # Clear the messages and add the summarized history as a single system message
        self.summary = summary
        self.system = self.system + f"\n\nSummary of Conversation so far: {summary}"
        self.messages = [{"role": "system", "content": self.system}]

    def get_total_tokens_in_message(self, message):
        """Returns the number of tokens in a message."""
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        num_tokens = len(encoding.encode(message))
        return num_tokens

    def get_total_tokens(self):
        """Returns the number of tokens in a text string."""
        total_tokens = 0
        for item in self.messages:
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            num_tokens = len(encoding.encode(item["content"]))
            total_tokens += num_tokens
        return total_tokens

    def load_memory(self):
        # Retrieve all memory items from the database
        self.cur.execute(
            "SELECT memory_item FROM memory ORDER BY interaction_index ASC desc"
        )
        results = self.cur.fetchall()
        memory_items = [json.loads(result[0]) for result in results]
        items_to_load = ""
        total_tokens = self.get_total_tokens()
        for item in memory_items:
            new_tokens = self.get_total_tokens_in_message(item["content"])
            if total_tokens + new_tokens < self.max_tokens:
                items_to_load += item["content"] + "\n"
            else:
                break

        self.messages = items_to_load
        self.conn.commit()

    def set_system(self, system):
        self.system = system
        self.messages[0] = {
            "role": "system",
            "content": self.system,
            "interaction_index": self.messages[0]["interaction_index"],
        }

    def create_tables(self):
        # Create the table if it doesn't exist
        self.cur.execute(
            """
        CREATE TABLE IF NOT EXISTS memory (
            interaction_index BIGINT PRIMARY KEY,
            memory_item JSONB NOT NULL,
            role TEXT NOT NULL
        )
        """
        )
        return


if __name__ == "__main__":
    # Example usage:
    memory_manager = MemoryManager(model="gpt-3.5-turbo-0613")

    # Add messages with interaction indices
    memory_manager.add_message("user", "What's the weather like in Boston?")
    memory_manager.add_message("assistant", "The weather in Boston is sunny.")
    memory_manager.add_message("user", "Tell me a joke.")
    # Archive a memory item manually
    idx = int(time.time() * 1000)  # Convert to integer here as well
    memory_manager.archive_memory_item(
        {"role": "user", "content": "This is a test message.", "interaction_index": idx}
    )

    # Retrieve the manually archived memory item
    memory_manager.display_conversation()
