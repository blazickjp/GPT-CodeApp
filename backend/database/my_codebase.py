import os
import datetime
import subprocess
from dotenv import load_dotenv
import openai
import numpy as np
import tiktoken

from sklearn.metrics.pairwise import cosine_similarity
from tenacity import (
    retry,
    wait_random_exponential,
    stop_after_attempt,
)
from psycopg2 import sql
from psycopg2.extensions import connection


EMBEDDING_MODEL = "text-embedding-ada-002"
ENCODER = tiktoken.encoding_for_model("gpt-3.5-turbo")
SUMMARY_MODEL = "gpt-3.5-turbo"
README_MODEL = "gpt-4"
SUMMARY_PROMPT = """
Please summarise the following what the following code is doing.
Please be consise and include all the important informastion.\n\n
CODE:{}
SUMMARY:
"""


def get_git_root(path="."):
    try:
        root = (
            subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=path)
            .decode("utf-8")
            .strip()
        )
        return root
    except Exception as e:
        print(e)
        return None


class MyCodebase:
    load_dotenv()
    IGNORE_DIRS = os.getenv("IGNORE_DIRS")
    FILE_EXTENSIONS = os.getenv("FILE_EXTENSIONS")

    def __init__(self, directory: str = ".", db_connection: connection = None):
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

    def set_directory(self, directory):
        self.directory = os.path.abspath(directory)
        self._update_files_and_embeddings()
        self.remove_old_files()

    def update_file(self, file_path):
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
                    print(f"File {file_path} is up to date")
                    return
                else:
                    print(f"Updating file {file_path}")

        embedding = list(self.encode(text))
        token_count = len(ENCODER.encode(text))
        embedding = np.array(embedding).tobytes()
        response = openai.ChatCompletion.create(
            model=SUMMARY_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": SUMMARY_PROMPT.format(text),
                },
            ],
            max_tokens=250,
            temperature=0.4,
        )
        file_summary = response["choices"][0]["message"]["content"].strip()

        # The dict's key is the file path, and value is a dict containing the text and embedding
        self.cur.execute(
            sql.SQL(
                """
                INSERT INTO files (file_path, text, embedding, token_count, summary, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (file_path)
                DO UPDATE SET text = %s, embedding = %s, token_count = %s, summary = %s, last_updated = %s
                """,
            ),
            (
                file_path,
                text,
                embedding,
                token_count,
                file_summary,
                last_modified,
                text,
                embedding,
                token_count,
                file_summary,
                last_modified,
            ),
        )
        self.conn.commit()

    def create_tables(self):
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

    @retry(
        wait=wait_random_exponential(min=1, max=20),
        stop=stop_after_attempt(6),
    )
    def encode(self, text_or_tokens, model=EMBEDDING_MODEL):
        result = openai.Embedding.create(input=text_or_tokens, model=model)
        return result["data"][0]["embedding"]

    def search(self, query, k=2):
        """
        Search for files that match the query.
        """
        self.cur.execute(
            """
            SELECT embedding, file_path FROM files
            """
        )
        file_embeddings = [
            (file[1], np.frombuffer(file[0])) for file in self.cur.fetchall()
        ]
        embeddings = np.array([file[1] for file in file_embeddings])
        file_list = [file[0] for file in file_embeddings]
        query_embedding = self.encode(query)
        query_embedding = np.array(query_embedding).reshape(1, -1)
        print(f"Query embedding shape: {query_embedding.shape}")
        print(f"Embeddings shape: {embeddings.shape}")
        similarities = cosine_similarity(query_embedding, embeddings)[0]
        print(f"Similarities shape: {similarities.shape}")

        # Ensure k is not greater than the total number of files
        k = min(k, len(file_list))

        # Sort by similarity
        sorted_indices = np.argsort(similarities)[::-1][:k]
        out_files = [file_list[i] for i in sorted_indices]
        print(out_files)

        # Return sorted file paths and content
        # results = []
        out = ""
        for file_name in out_files:
            self.cur.execute(
                sql.SQL(
                    """
                    SELECT text FROM files WHERE file_path = %s
                    """
                ),
                (file_name,),
            )
            content = self.cur.fetchall()[0][0]
            print(f"Search Result: {file_name}")
            out += f"File: {file_name}\nContent:\n{content}\n"

        return out

    def get_summaries(self):
        self.cur.execute("SELECT file_path, summary FROM files")
        results = self.cur.fetchall()
        out = {}
        for file_name, summary in results:
            out.update({file_name: summary})
        return out

    def get_file_contents(self):
        self.cur.execute("SELECT file_path, text FROM files")
        results = self.cur.fetchall()
        out = {}
        for file_name, text in results:
            out.update({file_name: text})
        return out

    def tree(self) -> str:
        """
        Return a string representing the tree of the files in the database.
        TODO: Configure start_from so it's not hardcoded
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
        for file_path in file_paths:
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

    def remove_old_files(self):
        """
        Remove files from the database that are no longer present in the codebase.
        """
        self.cur.execute("SELECT file_path FROM files")
        file_paths = [result[0] for result in self.cur.fetchall()]
        for file_path in file_paths:
            if not os.path.exists(file_path) or file_path in self.file_dict.keys():
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

    def _update_files_and_embeddings(self):
        for root, dirs, files in os.walk(self.directory):
            print(self.IGNORE_DIRS)
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            for file_name in files:
                if self._is_valid_file(file_name):
                    file_path = os.path.join(root, file_name)
                    self.update_file(file_path)

    @staticmethod
    def _is_valid_file(file_name):
        return (
            not file_name.startswith(".")
            and not file_name.startswith("_")
            and any(file_name.endswith(ext) for ext in MyCodebase.FILE_EXTENSIONS)
        )
