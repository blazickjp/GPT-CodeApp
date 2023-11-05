"""
Methods and CRUD operations for managing system prompts.
"""
from typing import Optional, Dict
import os


class SystemPromptHandler:
    def __init__(self, db_connection, identity=None, tree=None):
        self.conn = db_connection
        self.cur = self.conn.cursor()
        self.system_file_summaries = None
        self.system_file_contents = None
        # self.identity = "You are an AI Pair Programmer and a world class python developer helping the Human work on a project."
        self.identity = identity
        self.system_table_name = "default_system_prompt"
        self.files_in_prompt = None
        self.system = self.identity
        self.tree = tree
        self.create_tables()
        self.directory = self.get_directory()

    def get_directory(self) -> str:
        self.cur.execute(
            """
            SELECT value FROM config WHERE field = 'directory';
            """
        )
        result = self.cur.fetchone()
        return result[0] if result else None

    def set_system(self, input: dict = {}) -> None:
        """Set the system message."""
        self.directory = self.get_directory()
        # print(input)
        if input.get("system_prompt") is not None:
            print("Updating system prompt")
            self.system = input.get("system_prompt")
        else:
            self.system = (
                self.identity
                + "\n\n"  # noqa 503
                + "The following information is intended to aid in your responses to the User\n\n"  # noqa 503
                + "The project directory is setup as follows:\n"  # noqa 503
            )
            self.system = self.system + self.tree + "\n\n" if self.tree else ""

            if self.system_file_contents:
                self.system += (
                    "Related File Contents:\n" + self.system_file_contents + "\n\n"
                )

        self.cur.execute(f"DELETE FROM {self.system_table_name}")
        self.cur.execute(
            f"INSERT INTO {self.system_table_name} (role, content) VALUES (?, ?)",
            ("system", self.system),
        )
        return True

    def get_file_contents(self) -> Dict[str, str]:
        self.cur.execute("SELECT file_path, text FROM files")
        results = self.cur.fetchall()
        out = {}
        for file_name, text in results:
            out.update({os.path.relpath(file_name, self.directory): text})
        return out

    def set_files_in_prompt(self, include_line_numbers: Optional[bool] = None) -> None:
        """
        Sets the files in the prompt.

        Args:
            files (List[File]): A list of files to be set in the prompt.
            include_line_numbers (Optional[bool]): Whether to include line numbers in the prompt.
        """
        file_contents = self.get_file_contents()
        content = ""
        for k, v in file_contents.items():
            if k in self.files_in_prompt and include_line_numbers:
                v = self._add_line_numbers_to_content(v)
                content += f"{k}:\n{v}\n\n"
            elif k in self.files_in_prompt:
                content += f"{k}:\n{v}\n\n"

        self.system_file_contents = content
        self.set_system()
        return

    def _add_line_numbers_to_content(self, content: str) -> str:
        """
        Adds line numbers to the given content.

        Args:
            content (str): The content to add line numbers to.

        Returns:
            str: The content with line numbers added.
        """
        lines = content.split("\n")
        for i in range(len(lines)):
            lines[i] = f"{i + 1} {lines[i]}"
        return "\n".join(lines)

    def create_tables(self):
        """Create a table for system prompts if it doesn't exist."""
        try:
            self.cur.execute(
                """
                CREATE TABLE IF NOT EXISTS system_prompts (
                    id TEXT PRIMARY KEY,
                    prompt TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            self.conn.commit()

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
            print(e)
            print("Failed to create table.")
            raise e

    def create_prompt(self, prompt_id, prompt):
        """Create a new system prompt."""
        try:
            self.cur.execute(
                """
            INSERT INTO system_prompts (id, prompt) VALUES (?, ?)
            """,
                (prompt_id, prompt),
            )
            self.conn.commit()
        except Exception as e:
            print(e)
            print(f"Prompt '{prompt}' with ID '{prompt_id}' already exists.")
        return

    def read_prompt(self, prompt_id):
        """Read a system prompt by ID."""
        self.cur.execute(
            """
            SELECT * FROM system_prompts WHERE id = ?
            """,
            (prompt_id,),
        )
        return self.cur.fetchone()

    def update_prompt(self, prompt_id, new_prompt):
        """Update a system prompt by ID."""
        print(prompt_id)
        self.cur.execute(
            """
            UPDATE system_prompts
            SET prompt = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_prompt, prompt_id),
        )
        self.conn.commit()
        return

    def delete_prompt(self, prompt_id):
        """Delete a system prompt by ID."""
        if not prompt_id:
            self.cur.execute(
                """
                DELETE FROM system_prompts
                WHERE id is null;
                """
            )
        else:
            self.cur.execute(
                """
                DELETE FROM system_prompts WHERE id = ?
                """,
                (prompt_id,),
            )

        self.conn.commit()

    def list_prompts(self):
        """List all system prompts."""
        self.cur.execute(
            """
            SELECT * FROM system_prompts
            """
        )
        output = []
        for prompt in self.cur.fetchall():
            output.append({"name": prompt[0], "prompt": prompt[1]})

        print(self.cur.fetchall())
        return output
