import tiktoken
from typing import Optional, List
from datetime import datetime
from dotenv import load_dotenv
from memory.system_prompt_handler import SystemPromptHandler
from pydantic import BaseModel, Field
import instructor
from instructor import OpenAISchema
from openai import OpenAI, AsyncOpenAI

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
    Data class to add or remove information from the working context.
    """

    thought: str = Field(
        default=...,
        description="Always think first and document your thought process here.",
    )
    new_context: List[str] | None = Field(
        default=None,
        description="Valuable information from the conversation you want to keep in working context. Should be in the form of a statement.",
    )

    def execute(self, working_context: WorkingContext) -> None:
        if self.old_context:
            for context in self.old_context:
                working_context.remove_context(context)
        if self.new_context:
            for context in self.new_context:
                working_context.add_context(context)

        return working_context


class MemoryManager:
    # MemoryManager class manages interactions with the memory database
    # including initializing connections, creating tables, and
    # delegating to other classes that interact with the database.

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
            db_connection=self.conn,
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
                # f"""
                # WITH Exclude AS (
                #     SELECT interaction_index, last_idx
                #     FROM (
                #         select lag(interaction_index,1) over (order by interaction_index desc) as last_idx, *
                #         from {self.memory_table_name}
                #         )
                #     WHERE (content LIKE '/%' AND role = 'user')
                # ),
                # Filtered AS (
                #     SELECT *
                #     FROM {self.memory_table_name}
                #     WHERE interaction_index NOT IN (SELECT interaction_index FROM Exclude)
                #     and interaction_index NOT IN (SELECT last_idx FROM Exclude)
                # ),
                # t1 AS (
                #     SELECT role,
                #         content as full_content,
                #         COALESCE(summarized_message, content) as content,
                #         COALESCE(summarized_message_tokens, content_tokens) as tokens,
                #         SUM(COALESCE(summarized_message_tokens, content_tokens)) OVER (ORDER BY interaction_index DESC) as token_cum_sum
                #     FROM Filtered
                #     WHERE project_directory = ?
                #     ORDER BY interaction_index DESC
                # )
                # SELECT role, full_content, content, tokens
                # FROM t1
                # WHERE token_cum_sum <= ?;
                # """,
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
        for result in results[::-1]:
            messages.append(
                {"role": result[0], "content": result[2], "full_content": result[1]}
            )
        return messages

    def add_message(
        self,
        role: str,
        content: str,
        command: Optional[str] = None,
        function_response: Optional[str] = None,
    ) -> None:
        timestamp = datetime.now().isoformat()
        message_tokens = self.get_total_tokens_in_message(content)
        summary, summary_tokens = (
            self.summarize(content) if message_tokens > float("inf") else (None, None)
        )
        is_function_call = command is not None
        # Function response can be determined by lag is_function_call
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
        """Returns the number of tokens in a message."""
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

        update = await self.working_context.client.chat.completions.create(
            model="gpt-4-1106-preview",
            response_model=ContextUpdate,
            messages=messages,
        )

        self.working_context = update.execute(self.working_context)

        self.prompt_handler.set_system()

        return

    def set_directory(self, directory: str) -> None:
        self.project_directory = directory
        self.working_context.project_directory = directory
        self.prompt_handler.directory = directory
        self.prompt_handler.set_system()
        return
