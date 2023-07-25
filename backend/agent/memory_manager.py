# base
import json
import time
import sys
from typing import Optional, List
from uuid import uuid4
from datetime import datetime
import os

# third party
import token
import openai
import psycopg2
import tiktoken
from dotenv import load_dotenv


class MemoryManager:
    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        identity: str = None,
        tree: str = None,
        max_tokens: int = 1000,
    ) -> None:
        load_dotenv()
        CODEAPP_DB_NAME = os.getenv("CODEAPP_DB_NAME")
        CODEAPP_DB_USER = os.getenv("CODEAPP_DB_USER")
        CODEAPP_DB_PW = os.getenv("CODEAPP_DB_PW")
        CODEAPP_DB_HOST = os.getenv("CODEAPP_DB_HOST")

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
        try:
            auth = {
                "dbname": CODEAPP_DB_NAME,
                "user": CODEAPP_DB_USER,
                "password": CODEAPP_DB_PW,
                "host": CODEAPP_DB_HOST,
            }
            self.conn = psycopg2.connect(**auth)
            print("Successfully connected to database")
        except Exception as e:
            if (
                self.CODEAPP_DB_USER is None
                or self.CODEAPP_DB_USER == "USER_FROM_SETUP_STEP4"
            ):
                raise Exception(
                    """
                    Failed to connect to database.
                    Credentials not set or changed in .env file or .env file is missing.
                    Please set the following environment variables in the .env file in the root directory:
                    CODEAPP_DB_NAME, CODEAPP_DB_USER, CODEAPP_DB_PW, CODEAPP_DB_HOST
                    """
                )
            else:
                raise e
        self.cur = self.conn.cursor()
        self.create_tables()
        self.conn.commit()
        self.set_system()

    def get_messages(self, chat_box: Optional[bool] = None) -> List[dict]:
        self.cur.execute(
            """
            SELECT role, content
            FROM system_prompt;
            """
        )
        results = self.cur.fetchall()
        messages = [{"role": result[0], "content": result[1]} for result in results]
        max_tokens = 10000 if chat_box else self.max_tokens
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
            (max_tokens,),
        )
        results = self.cur.fetchall()
        for result in results[::-1]:
            messages.append(
                {"role": result[0], "content": result[2], "full_content": result[1]}
            )

        return messages

    def add_message(self, role: str, content: str) -> None:
        timestamp = datetime.now().isoformat()  # Current timestamp in milliseconds
        message_tokens = self.get_total_tokens_in_message(content)
        summary, summary_tokens = (
            self.summarize(content) if message_tokens > 500 else (None, None)
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

    def summarize(self, message: str) -> str:
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

    def get_total_tokens_in_message(self, message: str) -> int:
        """Returns the number of tokens in a message."""
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        num_tokens = len(encoding.encode(message))
        return num_tokens

    def get_total_tokens(self) -> int:
        """Returns the number of tokens in a text string."""
        total_tokens = 0
        for item in self.messages:
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            num_tokens = len(encoding.encode(item["content"]))
            total_tokens += num_tokens
        return total_tokens

    def set_system(self, input: dict = {}) -> None:
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
