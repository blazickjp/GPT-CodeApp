import openai
import numpy as np
import os
import psycopg2
import pickle
import tiktoken

# from typing import List
from sklearn.metrics.pairwise import cosine_similarity
from tenacity import (
    retry,
    wait_random_exponential,
    stop_after_attempt,
)
from psycopg2 import sql


EMBEDDING_MODEL = "text-embedding-ada-002"
ENCODER = tiktoken.encoding_for_model("gpt-3.5-turbo")
SUMMARY_MODEL = "gpt-3.5-turbo"
SUMMARY_PROMPT = """
Please summarise the following code. The code is part of a larger project and this summary will
be used to help the AI Assistant understand the codebase when being prompted with questions.
Please be consise and include all the important information.\n\n
CODE:{}
SUMMARY:
"""


class MyCodebase:
    """
    A class used to represent a local database of files and their embeddings.

    The class takes a directory as an argument during initialization and finds all Python
    files within that directory and its subdirectories. Each file's content is read and
    its embedding is generated using OpenAI's Embedding API. The files and their embeddings
    are then stored for later use.

    Methods
    -------
    encode(text_or_tokens: str, model: str = EMBEDDING_MODEL) -> np.ndarray:
        Generate the OpenAI embedding for the given text.

    search(query: str, k: int = 2) -> List[Tuple[str, str]]:
        Search for files that match the query and return a sorted list of file names
        and their content based on their similarity to the query.

    file_lookup(file_identifiers: List[str]) -> List[str]:
        Look up and return the content of the files given their names or paths.

    Example
    -------
    >>> db = LocalRepositoryDB(directory="../")
    >>> query_results = db.search(query="Your search query")
    >>> for file_name, content in query_results:
    ...     print(f"File: {file_name}\nContent: {content}\n\n")
    >>> file_contents = db.file_lookup(file_identifiers=["file1.py", "/path/to/file2.py"])
    >>> for content in file_contents:
    ...     print(f"Content: {content}\n\n")
    """

    def __init__(self, directory: str = "."):
        self.files = []
        self.embeddings = []
        self.file_dict = {}
        ignore_dirs = ["node_modules", ".next"]
        directory = os.path.abspath(directory)
        self.conn = psycopg2.connect(
            dbname="memory",
            user="joe",
            password="1234",
            host="localhost",
        )
        self.cur = self.conn.cursor()
        self.create_tables()

        # Read and embed the files
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file_name in files:
                if (
                    not file_name.startswith(".")
                    and not file_name.startswith("__init__")
                    and (file_name.endswith(".js") or file_name.endswith(".py"))
                ):
                    file_path = os.path.join(root, file_name)
                    print(f"Reading file: {file_path}")
                    self.update_file(file_path)

        # Build the embeddings array from the file_dict
        self.embeddings = np.array(
            [file["embedding"] for file in self.file_dict.values()]
        )

    def update_file(self, file_path):
        with open(file_path, "r") as file:
            text = file.read()
            embedding = pickle.dumps(self.encode(text))
            token_count = len(ENCODER.encode(text))
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
            INSERT INTO files (file_path, text, embedding, token_count, summary)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (file_path)
            DO UPDATE SET text = %s, embedding = %s, token_count = %s, summary = %s, last_updated = CURRENT_TIMESTAMP
            """,
                ),
                (
                    file_path,
                    text,
                    embedding,
                    token_count,
                    file_summary,
                    text,
                    embedding,
                    token_count,
                    file_summary,
                ),
            )
            self.conn.commit()

        # Update the embeddings array from the file_dict
        self.cur.execute(
            """
            SELECT embedding FROM files
        """
        )
        self.embeddings = np.array([bytes(file[0]) for file in self.cur.fetchall()])

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
            TRUNCATE TABLE files;
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
        query_embedding = self.encode(query)
        similarities = cosine_similarity([query_embedding], self.embeddings)[0]

        # Ensure k is not greater than the total number of files
        k = min(k, len(self.file_dict))

        # Sort by similarity
        sorted_indices = np.argsort(similarities)[::-1][:k]

        # Return sorted file paths and content
        results = [
            (path, self.file_dict[path]["text"])
            for path in np.array(list(self.file_dict.keys()))[sorted_indices]
        ]
        out = ""
        for file_name, content in results:
            out += f"File: {file_name}\nContent: {content}\n\n"

        return out

    def get_summaries(self):
        self.cur.execute("SELECT file_path, summary FROM files")
        results = self.cur.fetchall()
        out = {}
        for file_name, summary in results:
            out.update({file_name: summary})
        return out

    def tree(self, start_from="GPT-CodeApp"):
        """
        Return a string representing the tree of the files in the database.
        """
        tree = {}

        # Fetch file paths from the database
        self.cur.execute("SELECT file_path, summary FROM files")
        file_paths = [result[0] for result in self.cur.fetchall()]

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


if __name__ == "__main__":
    # Example usage:
    db = MyCodebase(directory="../")
    print(db.tree())
