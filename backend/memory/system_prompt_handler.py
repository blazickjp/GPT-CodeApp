from typing import Optional, Dict, List, Any
import os
import logging
import subprocess
import sqlite3

from traitlets import Bool

logger = logging.getLogger(__name__)


class SystemPromptHandler:
    def __init__(
        self,
        db_connection: sqlite3.Connection,
        identity: Optional[str] = None,
        tree: Optional[str] = None,
        working_context: Optional[str] = None,
    ):
        """
        Initialize the SystemPromptHandler with a database connection and optional identity, tree, and working context.

        Args:
            db_connection (sqlite3.Connection): The database connection.
            identity (Optional[str], optional): The identity of the system. Defaults to None.
            tree (Optional[str], optional): The directory tree. Defaults to None.
            working_context (Optional[str], optional): The working context. Defaults to None.
        """
        self.conn = db_connection
        self.cur = self.conn.cursor()
        self.system_file_summaries = None
        self.system_file_contents = None
        self.identity = identity
        self.files_in_prompt = []
        self.system = self.identity
        self.tree = tree
        self.create_tables()
        self.directory = self.get_directory()

    def get_directory(self) -> str:
        """Retrieve the project directory from the configuration.

        Returns:
            str: The project directory.
        """
        self.cur.execute("SELECT value FROM config WHERE field = 'directory';")
        result = self.cur.fetchone()
        return result[0] if result else None

    def set_system(self, input: Dict[str, Any] = {}) -> bool:
        """
        Set the system message and optionally attach a diff from the main branch.

        Args:
            input (Dict[str, Any], optional): A dictionary containing the 'system_prompt' key with a new system message. Defaults to {}.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        self.directory = self.get_directory()
        if "system_prompt" in input:
            self.system = input["system_prompt"]
        else:
            self.system = (
                self.identity
                + "\n\n"
                + "The following information is intended to aid in your responses to the User\n\n"
                + "The project directory is setup as follows:\n"
            )
            self.system += self.tree + "\n\n" if self.tree else ""
            if self.system_file_contents:
                self.system += (
                    "Related File Contents:\n" + self.system_file_contents + "\n\n"
                )

        # Attach a diff from the main branch to the system prompt if applicable.
        diff = self.generate_diff_from_main()
        # logging.warning("****\n\nDiff from main branch:\n\n", diff)
        if diff.stdout:
            self.system += "\n\nDiff from main branch:\n" + str(diff.stdout) + "\n\n"

        self.cur.execute("DELETE FROM system_prompt")
        self.cur.execute(
            "INSERT INTO system_prompt (role, content) VALUES (?, ?)",
            ("system", self.system),
        )
        self.conn.commit()
        return True

    def get_file_contents(self) -> Dict[str, str]:
        """Fetch file contents from the database and return a dictionary.

        Returns:
            Dict[str, str]: A dictionary mapping file paths to their contents.
        """
        self.cur.execute("SELECT file_path, text FROM files")
        results = self.cur.fetchall()
        # Filter results before dictionary comprehension
        filtered_results = [
            (file_name, text)
            for file_name, text in results
            if file_name in self.files_in_prompt
        ]
        return {
            os.path.relpath(file_name, self.directory): text
            for file_name, text in filtered_results
        }

    def set_files_in_prompt(
        self, anth: Optional[bool] = False, include_line_numbers: Optional[bool] = None
    ) -> None:
        """
        Set which files should be included in the system prompt, with options to annotate and include line numbers.

        Args:
            anth (Optional[bool]): Whether to annotate the files with tags. Defaults to False.
            include_line_numbers (Optional[bool]): Whether to include line numbers in the file contents. Defaults to None.
        """
        file_contents = self.get_file_contents()
        content = ""
        for k, v in file_contents.items():
            sanitized_k = k.replace("<", "&lt;").replace(
                ">", "&gt;"
            )  # Sanitize k to be a valid tag
            if k in self.files_in_prompt and include_line_numbers:
                v = self._add_line_numbers_to_content(v)
            content += (
                f"<{sanitized_k}>\n{v}\n</{sanitized_k}>\n\n"
                if anth
                else f"{sanitized_k}:\n{v}\n\n"
            )

        self.system_file_contents = content
        self.set_system()

    def _add_line_numbers_to_content(self, content: str) -> str:
        """
        Add line numbers to the content of a file.

        Args:
            content (str): The content of the file.

        Returns:
            str: The content of the file with line numbers added.
        """
        return "\n".join(
            f"{i + 1} {line}" for i, line in enumerate(content.split("\n"))
        )

    def create_tables(self) -> None:
        """Create tables for system prompts if they don't exist."""
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
            self.cur.execute(
                """
                CREATE TABLE IF NOT EXISTS system_prompt (
                    role VARCHAR(100),
                    content TEXT
                );
            """
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to create table: {e}")
            raise

    def generate_diff_from_main(self) -> subprocess.CompletedProcess:
        """
        Generate a diff from the main branch.

        Returns:
            subprocess.CompletedProcess: The result of the git diff command.
        """
        repo_path = self.directory  # Assuming the directory is the repo path
        command = ["git", "-C", repo_path, "diff", "release..main"]
        return subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

    def list_prompts(self) -> List[Dict[str, Any]]:
        """
        List all system prompts.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each containing the details of a system prompt.
        """
        self.cur.execute("SELECT * FROM system_prompts")
        return [
            {
                "id": prompt[0],
                "name": prompt[0],
                "prompt": prompt[1],
                "created_at": prompt[2],
                "updated_at": prompt[3],
            }
            for prompt in self.cur.fetchall()
        ]

    def update_prompt(self, prompt_id: str, new_prompt: str) -> bool:
        """
        Update a system prompt by its ID.

        Args:
            prompt_id (str): The ID of the prompt to update.
            new_prompt (str): The new prompt text.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        try:
            self.cur.execute(
                "UPDATE system_prompts SET prompt = ? WHERE id = ?",
                (new_prompt, prompt_id),
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update prompt: {e}")
            return False

    def delete_prompt(self, prompt_id: str) -> bool:
        """
        Delete a system prompt by its ID.

        Args:
            prompt_id (str): The ID of the prompt to delete.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """
        try:
            self.cur.execute(
                "DELETE FROM system_prompts WHERE id = ?",
                (prompt_id,),
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to delete prompt: {e}")
            return False

    def read_prompt(self, prompt_id: str) -> Bool():
        """
        Read a system prompt by its ID.

        Args:
            prompt_id (str): The ID of the prompt to read.

        Returns:
            Optional[str]: The prompt text if it exists, None otherwise.
        """
        self.cur.execute("SELECT prompt FROM system_prompts WHERE id = ?", (prompt_id,))
        result = self.cur.fetchone()
        return True if result else False

    def create_prompt(self, prompt: str) -> bool:
        """
        Create a new system prompt.

        Args:
            prompt (str): The prompt text.

        Returns:
            bool: True if the creation was successful, False otherwise.
        """
        try:
            self.cur.execute(
                "INSERT INTO system_prompts (prompt) VALUES (?)",
                (prompt,),
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to create prompt: {e}")
            return False


# Example usage:
# handler = SystemPromptHandler(db_connection)
# handler.set_system()
