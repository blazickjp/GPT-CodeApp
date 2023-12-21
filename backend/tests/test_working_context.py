import unittest
from memory.memory_manager import WorkingContext


class TestWorkingContext(unittest.TestCase):
    def test_add_context(self):
        # Test adding context
        working_context = WorkingContext(None, None)
        working_context.add_context("New context")
        self.assertIn("New context", working_context.context)

    def test_get_context(self):
        # Test getting full context
        working_context = WorkingContext(None, None)
        working_context.context = "Existing context"
        self.assertEqual(working_context.get_context(), "Existing context")

    def test_remove_context(self):
        # Test removing context
        working_context = WorkingContext(None, None)
        working_context.context = "Remove this context"
        working_context.remove_context("Remove this context")
        self.assertNotIn("Remove this context", working_context.context)
