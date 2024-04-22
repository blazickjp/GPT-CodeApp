# import unittest
# from unittest.mock import Mock
# from memory.memory_manager import WorkingContext


# class TestWorkingContext1(unittest.TestCase):
#     def setUp(self):
#         self.db_connection = Mock()
#         self.db_cursor = self.db_connection.cursor.return_value
#         self.project_directory = "./"
#         self.working_context = WorkingContext(
#             self.db_connection, self.project_directory
#         )

#     def test_create_tables(self):
#         self.working_context.create_tables()
#         self.db_cursor.execute.assert_called()

#     def test_add_context(self):
#         test_context = "Additional context"
#         self.working_context.add_context(test_context)
#         self.db_cursor.execute.assert_called()
#         self.db_connection.commit.assert_called()

#     def test_get_context(self):
#         self.db_cursor.fetchall.return_value = [("Context 1",), ("Context 2",)]
#         context = self.working_context.get_context()
#         self.db_cursor.execute.assert_called()
#         self.assertIn("Context 1", context)
#         self.assertIn("Context 2", context)

#     def test_remove_context(self):
#         test_context = "Remove this context"
#         self.working_context.remove_context(test_context)
#         self.db_cursor.execute.assert_called()
#         self.db_connection.commit.assert_called()

#     def test_str_representation(self):
#         self.db_cursor.fetchall.return_value = [("Context 1",), ("Context 2",)]
#         self.working_context.get_context()
#         str_representation = str(self.working_context)
#         self.assertIn("Context 1", str_representation)
#         self.assertIn("Context 2", str_representation)
