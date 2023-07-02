import os
import ast
import re
from langchain.document_loaders import DirectoryLoader
from langchain.docstore.document import Document
from pathlib import Path
from typing import List, Any, Optional


def _is_visible(p: Path) -> bool:
    """
    Checks if a path is visible (not hidden).

    Args:
        p (Path): The path to check.

    Returns:
        bool: True if the path is visible, False otherwise.
    """
    parts = p.parts
    for _p in parts:
        if _p.startswith("."):
            return False
    return True


class ClassCollector(ast.NodeVisitor):
    def __init__(self):
        self.classes = []

    def visit_ClassDef(self, node):
        """
        Visits a ClassDef node and collects the class definitions.

        Args:
            node: The ClassDef node.
        """
        self.classes.append(ast.unparse(node))
        self.generic_visit(node)

    def get_class_by_name(self, class_name: str) -> Optional[str]:
        """
        Retrieves a class definition by its name.

        Args:
            class_name (str): The name of the class.

        Returns:
            Optional[str]: The class definition as a string, or None if not found.
        """
        for class_def in self.classes:
            if f"class {class_name}" in class_def:
                return class_def
        return None


class PythonClassDirectoryLoader(DirectoryLoader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.docs = []

    def load_file(
        self, item: Path, path: Path, docs: List[Document], pbar: Optional[Any]
    ) -> None:
        """
        Loads a file from the directory and extracts class definitions.

        Args:
            item (Path): The file path.
            path (Path): The root directory path.
            docs (List[Document]): The list of documents to populate.
            pbar (Optional[Any]): Progress bar object.

        Returns:
            None
        """
        if item.is_file() and os.path.abspath(item).endswith(".py"):
            full_path = os.path.abspath(item)
            if full_path.endswith("__init__.py"):
                return
            if full_path.endswith(".json"):
                return
            if full_path.startswith("/Users/josephblazick/Documents/langchain/docs"):
                return
            if full_path.startswith("/Users/josephblazick/Documents/langchain/tests"):
                return
            if _is_visible(item.relative_to(path)) or self.load_hidden:
                try:
                    # Load the Python source code
                    with open(item, "r") as file:
                        code = file.read()

                    # Parse the code and extract class definitions
                    tree = ast.parse(code)
                    collector = ClassCollector()
                    collector.visit(tree)
                    classes = collector.classes

                    # Create a Document object for each class definition
                    for class_def in classes:
                        try:
                            class_name = re.search("(?<=class\s)\w+", class_def).group(
                                0
                            )  # Extract the class name
                            self.docs.append(
                                Document(
                                    page_content=class_def,
                                    metadata={
                                        "file_path": str(item),
                                        "class_name": class_name,
                                    },
                                )
                            )
                        except Exception as e:
                            print("Skipping class definition due to error: ", e)

                except Exception as e:
                    if self.silent_errors:
                        print(e)
                    else:
                        print(e)
                        print(os.path.abspath(item))
                        raise e
                finally:
                    if pbar:
                        pbar.update(1)

    def get_file_data(self, file_path: str) -> List[Document]:
        """
        Retrieves the document data for a specific file path.

        Args:
            file_path (str): The file path.

        Returns:
            List[Document]: The list of Document objects associated with the file path.
        """
        return [doc for doc in self.docs if doc.metadata["file_path"] == file_path]

    def get_class(self, class_name: str) -> List[Document]:
        """
        Retrieves the class definitions for a specific class name.

        Args:
            class_name (str): The name of the class.

        Returns:
            List[Document]: The list of Document objects containing the class definitions.
        """
        content = [
            doc.page_content
            for doc in self.docs
            if doc.metadata.get("class_name") == class_name
        ]
        return "\n".join(content)
