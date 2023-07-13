import sys
import token
import openai
import json
import time
import psycopg2
import tiktoken
from datetime import datetime
from uuid import uuid4


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

    def __init__(
        self, model="gpt-3.5-turbo", identity=None, tree=None, max_tokens=1000
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.system = None
        self.identity = (
            "You are an AI Pair Programmer and a world class python developer helping the Human work on a project."
            if not identity
            else identity
        )
        self.tree = tree
        self.system_file_summaries = None
        self.system_file_contents = None
        self.messages = []
        self.conn = psycopg2.connect(
            host="localhost", database="memory", user="joe", password="1234"
        )
        self.cur = self.conn.cursor()
        self.create_tables()
        self.conn.commit()
        self.set_system()

    def get_messages(self):
        self.cur.execute(
            """
            SELECT role, content
            FROM system_prompt;
            """
        )
        results = self.cur.fetchall()
        messages = [{"role": result[0], "content": result[1]} for result in results]
        self.cur.execute(
            """
            with t1 as (
                SELECT role,
                    content as full_content,
                    COALESCE(summarized_message, content) as content,
                    COALESCE(summarized_message_tokens, content_tokens) as tokens,
                    sum(COALESCE(summarized_message_tokens, content_tokens)) OVER (ORDER BY interaction_index DESC) as token_cum_sum
                FROM memory
                ORDER BY interaction_index desc
            )
            select role, full_content, content, tokens
            from t1
            WHERE token_cum_sum <= %s
            """,
            (self.max_tokens,),
        )
        results = self.cur.fetchall()
        tokens = 0
        for result in results[::-1]:
            tokens += result[3]
            if tokens > self.max_tokens:
                break
            messages.append(
                {"role": result[0], "content": result[2], "full_content": result[1]}
            )

        return messages

    def add_message(self, role, content):
        timestamp = datetime.now().isoformat()  # Current timestamp in milliseconds
        message_tokens = self.get_total_tokens_in_message(content)
        summary, summary_tokens = (
            self.summarize(content) if message_tokens > 200 else (None, None)
        )
        try:
            self.cur.execute(
                """
                INSERT INTO memory
                (interaction_index, role, content, content_tokens, summarized_message, summarized_message_tokens)
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                (
                    timestamp,
                    role,
                    content,
                    message_tokens,
                    summary,
                    summary_tokens,
                ),
            )
            self.conn.commit()
        except Exception as e:
            print("Failed to insert data: ", str(e))
        return

    def summarize(self, message):
        prompt = """Please summarize the following message. Reply only with the summary and do not
        include any other text in your response.
        MESSAGE: {}
        SUMMARY:
        """.format(
            message
        )
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=250,  # You can adjust this value
        )
        summary = response["choices"][0]["message"]["content"].strip()
        tokens = self.get_total_tokens_in_message(summary)
        return summary, tokens

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

    def set_system(self, input: dict = {}):
        """Set the system message."""

        "Update the system prompt manually"
        if len(input.keys()) != 0:
            self.system = input.get("system")
            return True

        system = (
            self.identity + "\n\n" + "********* Contextual Information *********\n\n"
        )
        system += (
            "The project directory is setup as follows:\n" + self.tree + "\n\n"
            if self.tree
            else ""
        )

        system += (
            "Summaries of Relted Files:\n" + self.system_file_summaries + "\n\n"
            if self.system_file_summaries
            else ""
        )
        system += (
            "Related File Contents:\n" + self.system_file_contents + "\n\n"
            if self.system_file_contents
            else ""
        )
        self.system = system

        self.cur.execute(
            """
            TRUNCATE TABLE system_prompt;
            INSERT INTO system_prompt
            (role, content, content_tokens, updated_at)
            VALUES (%s, %s, %s, %s)
            """,
            (
                "system",
                self.system,
                self.get_total_tokens_in_message(self.system),
                datetime.now().isoformat(),
            ),
        )

    def create_tables(self):
        # Create the table if it doesn't exist
        self.cur.execute(
            """
        CREATE TABLE IF NOT EXISTS memory (
            interaction_index TIMESTAMP DEFAULT NOW(),
            conversation_id TEXT,
            role TEXT,
            content TEXT,
            content_tokens INT,
            summarized_message TEXT,
            summarized_message_tokens INT
        );

        CREATE TABLE IF NOT EXISTS system_prompt (
            role TEXT,
            content TEXT,
            content_tokens INT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
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
