"""
This module contains the implementation of the memory management system for the backend. It includes the `WorkingContext` class, which is responsible for managing the working context of the user, including the database connection, project directory, and interaction with the OpenAI API client. The module also handles the creation of necessary database tables and provides methods for managing the working context data within the database. Additionally, it integrates with other components such as the system prompt handler and the OpenAI API client to facilitate the generation and management of system prompts and responses.
"""

import tiktoken
from typing import Optional, List
from datetime import datetime
from dotenv import load_dotenv
from memory.system_prompt_handler import SystemPromptHandler
from pydantic import BaseModel, Field
import instructor
from instructor import OpenAISchema
from openai import OpenAI, AsyncOpenAI
import logging

CLIENT = instructor.patch(AsyncOpenAI())


class WorkingContext:
    def __init__(self, db_connection, project_directory) -> None:
        """Initializes the WorkingContext class.

        Args:
          db_connection: The database connection object.
          project_directory: The path to the project directory.

        Attributes:
          context: The working context string.
          conn: The database connection.
          cur: The database cursor.
          client: The OpenAI API client.
          project_directory: The project directory path.

        """
        self.context = "The user is named Joe"
        self.conn = db_connection
        self.cur = self.conn.cursor()
        self.client = CLIENT
        self.project_directory = project_directory
        self.create_tables()

    def create_tables(self) -> None:
        try:
            self.cur.execute(
                """
                CREATE TABLE IF NOT EXISTS working_context
                (
                    context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    project_directory TEXT
                );
                """
            )
        except Exception as e:
            print("Failed to create tables: ", str(e))
        return

    def add_context(self, context: str) -> None:
        self.context += "\n" + context

        self.cur.execute(
            """
            INSERT INTO working_context
            (context, created_at, project_directory)
            VALUES (?, ?, ?);
            """,
            (context, datetime.now().isoformat(), self.project_directory),
        )
        self.conn.commit()

    def get_context(self) -> str:
        self.cur.execute(
            """
            SELECT context, created_at
            FROM working_context
            where project_directory = ?
            """,
            (self.project_directory,),
        )
        results = self.cur.fetchall()
        self.context = ""
        for result in results:
            self.context += "\n" + result[0]

        return self.context

    def remove_context(self, context: str) -> None:
        self.context = self.context.replace(context, "")
        self.cur.execute(
            """
            DELETE FROM working_context
            WHERE context = ?
            and project_directory = ?
            """,
            (context, self.project_directory),
        )
        self.conn.commit()

    def __str__(self) -> str:
        return self.context


class ContextUpdate(BaseModel):
    """
    API to add information from the working context.
    """

    thought: str = Field(
        default=...,
        description="Always think first and document your thought process here.",
    )
    new_context: List[str] | None = Field(
        default=None,
        description="Valuable information from the conversation you want to keep in working context. ",
    )

    def execute(self, working_context: WorkingContext) -> None:
        if self.new_context:
            for context in self.new_context:
                working_context.add_context(context)

        return working_context


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
        self.conn = db_connection
        self.cur = self.conn.cursor()
        self.working_context = WorkingContext(
            db_connection=db_connection, project_directory=self.project_directory
        )
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
        self.cur.execute(
            f"""
            SELECT role, content
            FROM {self.system_table_name};
            """
        )
        results = self.cur.fetchall()
        messages = [{"role": result[0], "content": result[1]} for result in results]

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
            if prev_role == result[0]:
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
        summary, summary_tokens = (
            self.summarize(content) if message_tokens > float("inf") else (None, None)
        )
        is_function_call = command is not None

        try:
            self.cur.execute(
                f"""
                INSERT INTO {self.memory_table_name}
                (interaction_index, role, content, content_tokens, summarized_message, summarized_message_tokens, project_directory, is_function_call)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
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
                    function_response BOOLEAN DEFAULT FALSE
                );
                """
            )
        except Exception as e:
            print("Failed to create tables: ", str(e))
        return

    async def update_context(self):
        ctx = self.working_context.get_context()
        print("Working Context: ", ctx)
        prompt = f"""
You are monitoring a conversation between an engineer and their AI Assistant.
Your mission is to manage the working memory for the AI Assistant. 
You do this by adding information to the working context (short-term memory) based on the conversation history.


## Guidelines
- Your insertions should be short, concise, and relevant to the future of the conversation.
- Keep track of facts, ideas, and concepts that are important to the conversation.
- Monitor the personality of the person you're speaking with and adjust your responses accordingly.
- Keep track of things that the user appeared to like or dislike.
- In your thoughts, justify why you are adding or removing information from the working context.

You can see the current working context below.

Working Context:
{ctx}

Please make any updates accordingly. Be sure the think step by step as you work.
"""
        messages = [
            {"role": item["role"], "content": item["content"]}
            for item in self.get_messages()
        ]

        for message in messages:
            if message["role"] == "system":
                message["content"] = prompt

        print(messages)

        update = await self.working_context.client.chat.completions.create(
            model="gpt-4-1106-preview",
            response_model=ContextUpdate,
            messages=messages,
        )

        print(update)

        self.working_context = update.execute(self.working_context)

        self.prompt_handler.set_system()

        return

    def set_directory(self, directory: str) -> None:
        self.project_directory = directory
        self.working_context.project_directory = directory
        self.prompt_handler.directory = directory
        self.prompt_handler.set_system()
        return
