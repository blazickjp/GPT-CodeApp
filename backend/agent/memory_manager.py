import openai
import os
import tiktoken

from typing import Optional, List
from datetime import datetime
from dotenv import load_dotenv
from psycopg2.extensions import connection


class MemoryManager:
    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        identity: str = None,
        tree: str = None,
        max_tokens: int = 1000,
        table_name: str = "default",
        db_connection: connection = None,
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
        self.messages = []
        self.memory_table_name = f"{table_name}_memory"
        self.system_table_name = f"{table_name}_system_prompt"
        self.conn = db_connection
        self.cur = self.conn.cursor()

        self.create_tables()
        self.conn.commit()
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
        self.cur.execute(
            f"""
            with t1 as (
                SELECT role,
                    content as full_content,
                    COALESCE(summarized_message, content) as content,
                    COALESCE(summarized_message_tokens, content_tokens) as tokens,
                    sum(COALESCE(summarized_message_tokens, content_tokens)) OVER (ORDER BY interaction_index DESC) as token_cum_sum
                FROM {self.memory_table_name}
                WHERE project_directory = %s
                ORDER BY interaction_index desc
            )
            select role, full_content, content, tokens
            from t1
            WHERE token_cum_sum <= %s
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

    def add_message(self, role: str, content: str) -> None:
        timestamp = datetime.now().isoformat()  # Current timestamp in milliseconds
        message_tokens = self.get_total_tokens_in_message(content)
        summary, summary_tokens = (
            self.summarize(content) if message_tokens > 500 else (None, None)
        )
        try:
            self.cur.execute(
                f"""
                INSERT INTO {self.memory_table_name}
                (interaction_index, role, content, content_tokens, summarized_message, summarized_message_tokens, project_directory)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
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
        if input.get("system"):
            self.system = input.get("system")
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

        self.cur.execute(
            f"""
            TRUNCATE TABLE {self.system_table_name};
            INSERT INTO {self.system_table_name}
            (role, content)
            VALUES (%s, %s);
            """,
            (
                "system",
                self.system,
            ),
        )
        self.conn.commit()
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
