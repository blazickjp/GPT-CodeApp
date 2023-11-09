import unittest
import os
from unittest.mock import Mock
from database.my_codebase import MyCodebase
from unittest.mock import patch

IGNORE_DIRS = ["node_modules", ".next", ".venv", "__pycache__", ".git"]
FILE_EXTENSIONS = [".js", ".py", ".md"]


class MyCodebaseTests(unittest.TestCase):
    DIRECTORY = os.path.dirname(os.path.abspath(__file__))
    DIRECTORY = os.path.join(DIRECTORY, "..", "..")
    print(DIRECTORY)

    def setUp(self):
        # Create a mock connection object
        conn = Mock()

        # Create a mock cursor object
        cursor = Mock()

        # Configure the mock connection to return the mock cursor when cursor() is called
        conn.cursor.return_value = cursor

        # Configure the mock cursor to return an empty list when fetchall() is called
        cursor.fetchall.return_value = []

        self.codebase = MyCodebase(
            self.DIRECTORY,
            db_connection=conn,
            ignore_dirs=IGNORE_DIRS,
            file_extensions=FILE_EXTENSIONS,
        )

    @patch(
        "database.my_codebase.ENCODER.encode", return_value=list(range(10))
    )  # mocks ENCODER.encode to always return a list of length 10
    def test_set_directory(self, mock_encode):
        new_directory = os.path.abspath("../")
        self.codebase.set_directory(new_directory)
        self.assertEqual(self.codebase.directory, os.path.abspath(new_directory))

    @patch(
        "database.my_codebase.ENCODER.encode", return_value=list(range(10))
    )  # mocks ENCODER.encode to always return a list of length 10
    def test_is_valid_file(self, mock_encode):
        self.assertTrue(self.codebase._is_valid_file("valid_file.py"))
        self.assertFalse(self.codebase._is_valid_file(".invalid_file.py"))
        self.assertFalse(self.codebase._is_valid_file("invalid_file.json"))
        self.assertFalse(self.codebase._is_valid_file("package-lock.json"))

    @patch(
        "database.my_codebase.ENCODER.encode", return_value=list(range(10))
    )  # mocks ENCODER.encode to always return a list of length 10
    def test_tree(self, mock_encode):
        tree = self.codebase.tree()
        self.assertIsInstance(tree, str)
