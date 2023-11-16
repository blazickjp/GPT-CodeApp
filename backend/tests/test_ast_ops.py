import unittest
from agent.agent_functions.ast_ops import (
    ASTChangeApplicator,
    AddFunction,
    DeleteFunction,
    ModifyFunction,
)


class TestASTOps(unittest.TestCase):
    def test_add_function(self):
        source_code = "def existing_function():\n    pass\n"
        add_function_op = AddFunction(
            file_name="example.py",  # Include the missing file_name field
            function_name="new_function",
            args="",
            body="return 'hello world'",
            decorator_list=[],
            returns=None,
        )

        applicator = ASTChangeApplicator(source_code)
        modified_code = applicator.apply_changes([add_function_op])

        self.assertIn("def new_function():", modified_code)
        self.assertIn("return 'hello world'", modified_code)

    def test_delete_function(self):
        source_code = """
def function_to_delete():
    pass

def keep_me():
    pass
"""
        delete_function_op = DeleteFunction(
            file_name="test.py", function_name="function_to_delete"
        )

        applicator = ASTChangeApplicator(source_code)
        modified_code = applicator.apply_changes([delete_function_op])

        self.assertNotIn("def function_to_delete():", modified_code)
        self.assertIn("def keep_me():", modified_code)

    def test_modify_function(self):
        source_code = "def function_to_modify(a, b):\n    return a + b\n"
        modify_function_op = ModifyFunction(
            file_name="test.py",
            function_name="function_to_modify",
            new_body="return a * b",
        )

        applicator = ASTChangeApplicator(source_code)
        modified_code = applicator.apply_changes([modify_function_op])

        self.assertIn("return a * b", modified_code)


# Add more tests for other operations: AddClass, DeleteClass, ModifyClass, etc.


if __name__ == "__main__":
    unittest.main()
