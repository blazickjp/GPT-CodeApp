import os
import datetime
from dotenv import load_dotenv
import tiktoken
from typing import Dict


EMBEDDING_MODEL = "text-embedding-ada-002"
ENCODER = tiktoken.encoding_for_model("gpt-3.5-turbo")
SUMMARY_MODEL = "gpt-3.5-turbo"
README_MODEL = "gpt-4"
SUMMARY_PROMPT = """
Please summarise, in bullet points, what the following code is doing.
Please be consise and include all the important informastion.\n\n
CODE:{}
SUMMARY:
"""


# new comment
class MyCodebase:
    load_dotenv()
    IGNORE_DIRS = os.getenv("IGNORE_DIRS")
    FILE_EXTENSIONS = os.getenv("FILE_EXTENSIONS")
    UPDATE_FULL = os.getenv("AUTO_UPDATE_EMBEDDINGS", False)

    def __init__(self, directory: str = ".", db_connection=None):
        self.directory = directory
        self.conn = db_connection
        self.cur = self.conn.cursor()
        self.create_tables()
        self._update_files_and_embeddings()
        self.remove_old_files()

    def set_directory(self, directory: str) -> None:
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

    def get_file_contents(self) -> Dict[str, str]:
        self.cur.execute("SELECT file_path, text FROM files")
        results = self.cur.fetchall()
        out = {}
        for file_name, text in results:
            out.update({os.path.relpath(file_name, self.directory): text})
        print(f"\n\nGet File Contents: {out.keys()}")
        return out

    def tree(self) -> str:
        tree = {}
        start_from = os.path.basename(self.directory)
        print("Start from: ", start_from)

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
            if not os.path.exists(file_path):
                self.cur.execute(
                    """
                    DELETE FROM files WHERE file_path = ?
                    """,
                    (file_path,),
                )
                self.conn.commit()
                print(f"****    Removed file {file_path} from the database    *****")

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

    @staticmethod
    def _is_valid_file(file_name):
        return (
            not file_name.startswith(".")
            and not file_name.startswith("_")  # noqa 503
            and any(  # noqa 503
                file_name.endswith(ext) for ext in MyCodebase.FILE_EXTENSIONS
            )
        ) or file_name == "Dockerfile"

    @staticmethod
    def _is_valid_directory(directory: str) -> bool:
        return (
            not directory.startswith(".")
            and not directory.startswith("_")  # noqa 503
            and directory not in MyCodebase.IGNORE_DIRS  # noqa 503
        )
