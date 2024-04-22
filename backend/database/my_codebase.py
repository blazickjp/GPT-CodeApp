"""
This module defines the MyCodebase class, which is responsible for managing the database operations related to codebase management. It includes functionalities such as initializing the database connection, setting up the directory to scan for code, creating necessary database tables, updating files and embeddings, and removing old files from the database. The class utilizes an external encoder (tiktoken) for encoding model specifics and interacts with the database to store and manage the codebase information efficiently.
"""

import os
import datetime
import tiktoken


ENCODER = tiktoken.encoding_for_model("gpt-3.5-turbo")


class MyCodebase:
    UPDATE_FULL = False

    def __init__(
        self,
        directory: str = ".",
        db_connection=None,
        ignore_dirs=None,
        file_extensions=None,
    ):
        self.directory = directory
        self.conn = db_connection
        self.cur = self.conn.cursor()
        self.ignore_dirs = ignore_dirs
        self.file_extensions = file_extensions
        self.create_tables()
        self._update_files_and_embeddings()
        self.remove_old_files()

    def set_directory(self, directory: str) -> None:
        """
        Sets the root directory to scan for code.

        This updates the 'directory' value in the config table of the database,
        and triggers a re-scan of all files and embeddings. It also removes any old files that
        are no longer in the directory.

        Args:
        directory (str): The path to the new root directory to scan.
        """
        print(f"Setting directory to {directory}")
        self.directory = directory
        self.cur.execute(
            """
            INSERT INTO config (field, value, last_updated)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(field)
            DO UPDATE SET value = excluded.value, last_updated = excluded.last_updated
            WHERE field = 'directory';
            """,
            ("directory", directory),
        )
        self.conn.commit()
        self._update_files_and_embeddings()
        self.remove_old_files()

    def get_directory(self) -> str:
        self.cur.execute(
            """
            SELECT value FROM config WHERE field = 'directory';
            """
        )
        result = self.cur.fetchone()
        return result[0] if result else None

    def update_file(self, file_path: str) -> None:
        self.cur.execute(
            """
            SELECT last_updated FROM files WHERE file_path = ?
            """,
            (file_path,),
        )
        result = self.cur.fetchall()
        with open(file_path, "r") as file:
            text = file.read()
            last_modified = datetime.datetime.fromtimestamp(
                os.path.getmtime(file_path)
            ).replace(microsecond=0)

            if len(result) > 0:
                db_time = datetime.datetime.strptime(result[0][0], "%Y-%m-%d %H:%M:%S")

                if db_time >= last_modified:
                    return
                else:
                    print(f"Updating file {file_path}")

        token_count = len(ENCODER.encode(text))
        # The dict's key is the file path, and value is a dict containing the text and embedding
        self.cur.execute(
            """
            INSERT INTO files (file_path, text, token_count, last_updated)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(file_path)
            DO UPDATE SET text = excluded.text, token_count = excluded.token_count, last_updated = excluded.last_updated;
            """,
            (file_path, text, token_count, last_modified),
        )
        self.conn.commit()

    def create_tables(self) -> None:
        """
        Creates the necessary tables in the database if they don't exist.
        """
        try:
            self.cur.execute(
                """
                CREATE TABLE IF NOT EXISTS files (
                    file_path TEXT PRIMARY KEY,
                    text TEXT,
                    embedding BLOB,
                    token_count INT,
                    summary TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            self.conn.commit()

            self.cur.execute(
                """
                CREATE TABLE IF NOT EXISTS config (
                    field TEXT PRIMARY KEY,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            self.conn.commit()
        except Exception as e:
            print(f"Failed to create tables: {e}")

    def tree(self) -> str:
        """
        Generates a visual representation of the project's directory structure.

        This method fetches the file paths and summaries from the database, constructs a tree
        structure representing the directory hierarchy, and then generates a string representation
        of this tree. Each node in the tree represents a directory or file, with directories containing
        nested dictionaries of their contents.

        Returns:
            str: A string representation of the directory tree, with each node prefixed by "+--" and
                 indented to represent its depth in the hierarchy.
        """
        tree = {}
        start_from = os.path.basename(self.directory)

        # Fetch file paths from the database
        self.cur.execute("SELECT file_path, summary FROM files")
        file_paths = [
            result[0]
            for result in self.cur.fetchall()
            if result[0].startswith(self.directory)
        ]
        # Insert each file into the tree structure
        for file_path in sorted(file_paths):
            parts = file_path.split(os.path.sep)
            # Find the start_from directory in the path and trim up to it
            if start_from in parts:
                parts = parts[parts.index(start_from) :]
            current_level = tree
            for part in parts:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]

        # Function to recursively build the tree string
        def build_tree_string(current_level, indent=""):
            tree_string = ""
            for part in current_level:
                tree_string += f"{indent}+--{part}\n"
                tree_string += build_tree_string(current_level[part], indent + "    ")
            return tree_string

        # Build the tree string starting from the root
        return build_tree_string(tree)

    def remove_old_files(self) -> None:
        """
        Remove files from the database that are no longer present in the codebase.
        """
        self.cur.execute("SELECT file_path FROM files")
        file_paths = [result[0] for result in self.cur.fetchall()]
        for file_path in file_paths:
            if not os.path.exists(file_path) or not self._is_valid_file(file_path):
                self.cur.execute(
                    """
                    DELETE FROM files WHERE file_path = ?
                    """,
                    (file_path,),
                )
                self.conn.commit()

    def _update_files_and_embeddings(self) -> None:
        for root, dirs, files in os.walk(self.directory):
            dirs[:] = [d for d in dirs if self._is_valid_directory(d)]
            for file_name in files:
                if self._is_valid_file(file_name):
                    file_path = os.path.join(root, file_name)
                    try:
                        self.update_file(file_path)
                    except Exception as e:
                        print(f"Error updating file {file_path}: {e}")
                    self.remove_old_files()

    def _is_valid_file(self, file_name):
        return (
            not file_name.startswith(".")
            and not file_name.startswith("_")  # noqa 503
            and not file_name.endswith(".jsonl")  # noqa 503
            and any(  # noqa 503
                file_name.endswith(ext) for ext in self.file_extensions  # noqa 503
            )
        ) or file_name == "Dockerfile"

    def _is_valid_directory(self, directory: str) -> bool:
        return (
            not directory.startswith(".")
            and not directory.startswith("_")  # noqa 503
            and directory not in self.ignore_dirs  # noqa 503
        )
