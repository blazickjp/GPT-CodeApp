import os
import datetime
from dotenv import load_dotenv
import numpy as np
import tiktoken

from sklearn.metrics.pairwise import cosine_similarity
from psycopg2 import sql
from psycopg2.extensions import connection
from typing import List, Optional, Dict


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

    def __init__(
        self, directory: str = ".", db_connection: Optional[connection] = None
    ):
        self.files = []
        self.embeddings = []
        self.file_dict = {}
        self.directory = os.path.abspath(directory)
        self.conn = db_connection
        self.cur = self.conn.cursor()
        self.create_tables()
        self._update_files_and_embeddings()
        self.remove_old_files()
        self.embeddings = np.array(
            [file["embedding"] for file in self.file_dict.values()]
        )

    def set_directory(self, directory: str) -> None:
        self.directory = os.path.abspath(directory)
        self._update_files_and_embeddings()
        self.remove_old_files()

    def update_file(self, file_path: str) -> None:
        self.cur.execute(
            sql.SQL(
                """
                SELECT last_updated FROM files WHERE file_path = %s
                """
            ),
            (file_path,),
        )
        self.conn.commit()
        result = self.cur.fetchall()
        with open(file_path, "r") as file:
            text = file.read()
            last_modified = datetime.datetime.fromtimestamp(
                os.path.getmtime(file_path)
            ).replace(microsecond=0)

            if len(result) > 0:
                if result[0][0] >= last_modified:
                    return
                else:
                    print(f"Updating file {file_path}")

        token_count = len(ENCODER.encode(text))
        # The dict's key is the file path, and value is a dict containing the text and embedding
        self.cur.execute(
            sql.SQL(
                """
                INSERT INTO files (file_path, text, token_count, last_updated)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (file_path)
                DO UPDATE SET text = %s, token_count = %s, last_updated = %s
                """,
            ),
            (
                file_path,
                text,
                token_count,
                last_modified,
                text,
                token_count,
                last_modified,
            ),
        )
        self.conn.commit()

    def create_tables(self) -> None:
        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                file_path TEXT PRIMARY KEY,
                text TEXT,
                embedding BYTEA,
                token_count INT,
                summary TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        )
        self.conn.commit()

    def get_summaries(self) -> Dict[str, str]:
        self.cur.execute("SELECT file_path, summary FROM files")
        results = self.cur.fetchall()
        out = {}
        for file_name, summary in results:
            out.update({file_name: summary})
        return out

    def get_file_contents(self) -> Dict[str, str]:
        self.cur.execute("SELECT file_path, text FROM files")
        results = self.cur.fetchall()
        out = {}
        for file_name, text in results:
            out.update({file_name: text})
        return out

    def tree(self) -> str:
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
            if not os.path.exists(file_path):
                self.cur.execute(
                    sql.SQL(
                        """
                        DELETE FROM files WHERE file_path = %s
                        """
                    ),
                    (file_path,),
                )
                self.conn.commit()
                print(f"****    Removed file {file_path} from the database    *****")

    def _update_files_and_embeddings(self) -> None:
        for root, dirs, files in os.walk(self.directory):
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
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
            and not file_name.startswith("_")
            and any(file_name.endswith(ext) for ext in MyCodebase.FILE_EXTENSIONS)
        ) or file_name == "Dockerfile"
