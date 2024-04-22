"""
This module contains the implementation of the memory management system for the backend. It includes the `WorkingContext` class, which is responsible for managing the working context of the user, including the database connection, project directory, and interaction with the OpenAI API client. The module also handles the creation of necessary database tables and provides methods for managing the working context data within the database. Additionally, it integrates with other components such as the system prompt handler and the OpenAI API client to facilitate the generation and management of system prompts and responses.
"""

import tiktoken
from typing import Optional, List
from datetime import datetime
from dotenv import load_dotenv
from memory.system_prompt_handler import SystemPromptHandler
import instructor
from openai import AsyncOpenAI

from memory.working_context import WorkingContext

CLIENT = instructor.patch(AsyncOpenAI())


class MemoryManager:
    def __init__(
        self,
        model: str = "gpt-3.5-turbo-16k",
        identity: str = None,
        tree: str = None,
        max_tokens: int = 1000,
        table_name: str = "default",
        db_connection=None,
    ) -> None:
        load_dotenv()
        self.project_directory = None
        self.model = model
        self.max_tokens = max_tokens
        self.system = None
        self.identity = (
            "You are an AI Pair Programmer and a world class python developer helping the Human work on a project."
            if not identity
            else identity
        )
        self.system_file_summaries = None
        self.system_file_contents = None
        if db_connection is not None:
            self.conn = db_connection
        else:
            raise ValueError("db_connection cannot be None")
        self.cur = self.conn.cursor()
        self.cur = self.conn.cursor()
        self.working_context = WorkingContext()
        self.prompt_handler = SystemPromptHandler(
            db_connection=db_connection,
            tree=tree,
            identity=self.identity,
            working_context=self.working_context,
        )
        self.memory_table_name = f"{table_name}_memory"
        self.prompt_handler.system_table_name = f"{table_name}_system_prompt"
        self.system_table_name = f"{table_name}_system_prompt"
        self.create_tables()
        self.prompt_handler.set_system()
        self.background_tasks = None

    def get_messages(self, chat_box: Optional[bool] = None) -> List[dict]:
        """
        Fetches messages from the system prompt table.

        This method queries the system prompt table for messages, filtering based on the chat_box flag. If chat_box is True, it fetches messages with a higher token limit to accommodate more verbose interactions typical in a chat interface. Otherwise, it uses the default max_tokens limit defined for the system.

        Args:
            chat_box (Optional[bool]): A flag indicating whether the messages are being fetched for a chat box interface. Defaults to None.

        Returns:
            List[dict]: A list of dictionaries, each containing the role and content of a message.
        """
        messages = [{"role": "system", "content": self.prompt_handler.system}]

        max_tokens = 30000 if chat_box else self.max_tokens
        if chat_box:
            self.cur.execute(
                f"""
                with t1 as (
                    SELECT role,
                        content as full_content,
                        COALESCE(summarized_message, content) as content,
                        COALESCE(summarized_message_tokens, content_tokens) as tokens,
                        sum(COALESCE(summarized_message_tokens, content_tokens)) OVER (ORDER BY interaction_index DESC) as token_cum_sum
                    FROM {self.memory_table_name}
                    WHERE project_directory = ?
                    ORDER BY interaction_index desc
                )
                select role, full_content, content, tokens
                from t1
                WHERE token_cum_sum <= ?;
                """,
                (
                    self.project_directory,
                    max_tokens,
                ),
            )
        else:
            self.cur.execute(
                f"""
                with t1 as (
                    SELECT role,
                        content as full_content,
                        COALESCE(summarized_message, content) as content,
                        COALESCE(summarized_message_tokens, content_tokens) as tokens,
                        sum(COALESCE(summarized_message_tokens, content_tokens)) OVER (ORDER BY interaction_index DESC) as token_cum_sum
                    FROM {self.memory_table_name}
                    WHERE project_directory = ?
                    ORDER BY interaction_index desc
                )
                select role, full_content, content, tokens
                from t1
                WHERE token_cum_sum <= ?;
                """,
                (
                    self.project_directory,
                    max_tokens,
                ),
            )
        results = self.cur.fetchall()
        prev_role = "assistant"
        for result in results[::-1]:
            if prev_role == result[0] or result[2] == "":
                continue
            messages.append(
                {"role": result[0], "content": result[2], "full_content": result[1]}
            )
            prev_role = result[0]
        return messages

    def add_message(
        self,
        role: str,
        content: str,
        command: Optional[str] = None,
        function_response: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> None:
        """
        Adds a message to the memory database.

        This method inserts a new message into the memory database with the provided role, content, and optional command and function response. It also calculates the timestamp, the total number of tokens in the message, and optionally summarizes the message if the number of tokens exceeds a certain threshold.

        Args:
            role (str): The role of the message sender (e.g., "user" or "assistant").
            content (str): The content of the message.
            command (Optional[str]): An optional command associated with the message.
            function_response (Optional[str]): An optional function response associated with the message.

        Returns:
            None
        """
        timestamp = datetime.now().isoformat()
        message_tokens = self.get_total_tokens_in_message(content)
        summary, summary_tokens = (None, None)
        is_function_call = command is not None

        try:
            self.cur.execute(
                f"""
                INSERT INTO {self.memory_table_name}
                (interaction_index, role, content, content_tokens, summarized_message, summarized_message_tokens, project_directory, is_function_call, system_prompt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    timestamp,
                    role,
                    content,
                    message_tokens,
                    summary,
                    summary_tokens,
                    self.project_directory,
                    is_function_call,
                    system_prompt,
                ),
            )
            self.conn.commit()
        except Exception as e:
            print("Failed to insert data: ", str(e))
        return

    def get_total_tokens_in_message(self, message: str) -> int:
        """
        Calculates the total number of tokens in a given message using the tiktoken library.

        Args:
            message (str): The message for which to calculate the total number of tokens.

        Returns:
            int: The total number of tokens in the message.
        """
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        num_tokens = len(encoding.encode(message))
        return num_tokens

    def create_tables(self) -> None:
        try:
            self.cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.memory_table_name}
                (
                    interaction_index TIMESTAMP PRIMARY KEY,
                    role VARCHAR(100),
                    content TEXT,
                    content_tokens INT,
                    summarized_message TEXT,
                    summarized_message_tokens INT,
                    project_directory TEXT,
                    is_function_call BOOLEAN DEFAULT FALSE,
                    function_response BOOLEAN DEFAULT FALSE,
                    system_prompt TEXT DEFAULT NULL
                );
                """
            )
            self.conn.commit()
        except Exception as e:
            print("Failed to create tables: ", str(e))
        return

    def set_directory(self, directory: str) -> None:
        self.project_directory = directory
        self.working_context.project_directory = directory
        self.prompt_handler.directory = directory
        self.prompt_handler.set_system()
        return
