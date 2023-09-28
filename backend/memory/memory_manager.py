import os
import tiktoken
import sqlite3

from typing import Optional, List
from datetime import datetime
from dotenv import load_dotenv
from memory.system_prompt_handler import SystemPromptHandler


class MemoryManager:
    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        identity: str = None,
        tree: str = None,
        max_tokens: int = 5000,
        table_name: str = "default",
        db_connection=None,
    ) -> None:
        load_dotenv()
        self.project_directory = os.getenv("PROJECT_DIRECTORY")
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
        self.memory_table_name = f"{table_name}_memory"
        self.system_table_name = f"{table_name}_system_prompt"
        self.conn = db_connection
        self.cur = self.conn.cursor()
        self.prompt_handler = SystemPromptHandler(db_connection=self.conn)

        self.create_tables()
        self.set_system()

    def get_messages(self, chat_box: Optional[bool] = None) -> List[dict]:
        self.cur.execute(
            f"""
            SELECT role, content
            FROM {self.system_table_name};
            """
        )
        results = self.cur.fetchall()
        messages = [{"role": result[0], "content": result[1]} for result in results]

        max_tokens = 10000 if chat_box else self.max_tokens
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
                WHERE token_cum_sum <= ?
                """,
                (
                    self.project_directory,
                    max_tokens,
                ),
            )
        else:
            self.cur.execute(
                f"""
                WITH Exclude AS (
                    SELECT interaction_index, last_idx
                    FROM (
                        select lag(interaction_index,1) over (order by interaction_index desc) as last_idx, * 
                        from {self.memory_table_name}
                        )
                    WHERE (content LIKE '/%' AND role = 'user')
                ),
                Filtered AS (
                    SELECT *
                    FROM {self.memory_table_name}
                    WHERE interaction_index NOT IN (SELECT interaction_index FROM Exclude)
                    and interaction_index NOT IN (SELECT last_idx FROM Exclude)
                ),
                t1 AS (
                    SELECT role,
                        content as full_content,
                        COALESCE(summarized_message, content) as content,
                        COALESCE(summarized_message_tokens, content_tokens) as tokens,
                        SUM(COALESCE(summarized_message_tokens, content_tokens)) OVER (ORDER BY interaction_index DESC) as token_cum_sum
                    FROM Filtered
                    WHERE project_directory = ?
                    ORDER BY interaction_index DESC
                )
                SELECT role, full_content, content, tokens
                FROM t1
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

        # messsages = []
        # SPECIAL = "/"
        # for result in results:
        #     # Skip command messages and responses
        #     if result[0] == "user" and result[1].startswith(SPECIAL):
        #         continue
        #     if messsages[-1]["role"] == "user" and messages[-1]["content"].startswith(
        #         SPECIAL
        #     ):
        #         continue

        #     messsages.append({"role": result[0], "content": result[1]})

    def add_message(self, role: str, content: str) -> None:
        timestamp = datetime.now().isoformat()  # Current timestamp in milliseconds
        message_tokens = self.get_total_tokens_in_message(content)
        summary, summary_tokens = (
            self.summarize(content) if message_tokens > float("inf") else (None, None)
        )
        try:
            self.cur.execute(
                f"""
                INSERT INTO {self.memory_table_name}
                (interaction_index, role, content, content_tokens, summarized_message, summarized_message_tokens, project_directory)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    timestamp,
                    role,
                    content,
                    message_tokens,
                    summary,
                    summary_tokens,
                    self.project_directory,
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

    def set_system(self, input: dict = {}) -> None:
        """Set the system message."""

        "Update the system prompt manually"
        # print(input)
        print(input.keys())
        if input.get("system_prompt") is not None:
            print("Updating system prompt")
            self.system = input.get("system_prompt")
        else:
            self.system = (
                self.identity
                + "\n\n"  # noqa 503
                + "********* Contextual Information *********\n\n"  # noqa 503
            )
            self.system += (
                "The project directory is setup as follows:\n" + self.tree + "\n\n"
                if self.tree
                else ""
            )

            self.system += (
                "Summaries of Relted Files:\n" + self.system_file_summaries + "\n\n"
                if self.system_file_summaries
                else ""
            )
            self.system += (
                "Related File Contents:\n" + self.system_file_contents + "\n\n"
                if self.system_file_contents
                else ""
            )

        self.cur.execute(f"DELETE FROM {self.system_table_name}")
        self.cur.execute(
            f"INSERT INTO {self.system_table_name} (role, content) VALUES (?, ?)",
            ("system", self.system),
        )
        return True

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
                    project_directory TEXT
                );
                """
            )
            self.cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.system_table_name}
                (
                    role VARCHAR(100),
                    content TEXT
                );
                """
            )
            self.conn.commit()
        except Exception as e:
            print("Failed to create tables: ", str(e))
        return

    def reset_identity(self):
        self.identity = "You are an AI Pair Programmer and a world class python developer helping the Human work on a project."
        self.set_system()
        return True
