import unittest
import os
from ..database.my_codebase import MyCodebase


class MyCodebaseTests(unittest.TestCase):
    def setUp(self):
        self.codebase = MyCodebase(directory="../")
        print(self.codebase.directory)

    def test_set_directory(self):
        new_directory = os.path.abspath("../")
        self.codebase.set_directory(new_directory)
        self.assertEqual(self.codebase.directory, os.path.abspath(new_directory))

    def test_is_valid_file(self):
        self.assertTrue(self.codebase._is_valid_file("valid_file.py"))
        self.assertFalse(self.codebase._is_valid_file(".invalid_file.py"))

    def test_search(self):
        search_results = self.codebase.search("search_term")
        self.assertIsInstance(search_results, str)

    def test_get_summaries(self):
        summaries = self.codebase.get_summaries()
        self.assertIsInstance(summaries, dict)

    def test_get_file_contents(self):
        contents = self.codebase.get_file_contents()
        self.assertIsInstance(contents, dict)

    def test_tree(self):
        tree = self.codebase.tree()
        self.assertIsInstance(tree, str)


if __name__ == "__main__":
    unittest.main()
