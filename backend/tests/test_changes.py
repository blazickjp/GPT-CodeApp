import unittest
import ast
from agent.agent_functions.new_changes import VariableNameChange, CustomASTTransformer


class TestVariableNameChange(unittest.TestCase):
    def test_variable_rename(self):
        source_code = "x = 1"
        expected_code = "y = 1"

        # Parse the source code into an AST
        ast_tree = ast.parse(source_code)

        # Create a VariableNameChange instance for the rename operation
        rename_change = VariableNameChange(original_name="x", new_name="y")

        # Apply the change using the CustomASTTransformer
        transformer = CustomASTTransformer(changes=[rename_change])
        new_ast_tree = transformer.visit(ast_tree)

        # Convert the new AST back to source code
        new_source_code = ast.unparse(new_ast_tree)

        # Assert that the new source code matches the expected code
        self.assertEqual(expected_code, new_source_code)

    def test_variable_rename2(self):
        source_code = """
def example_function():
    x = 1
    print(x)
"""
        expected_code = """
def example_function():
    y = 1
    print(y)
"""

        # Parse the source code into an AST
        ast_tree = ast.parse(source_code)

        # Create a VariableNameChange instance for the rename operation
        rename_change = VariableNameChange(original_name="x", new_name="y")

        # Apply the change using the CustomASTTransformer
        transformer = CustomASTTransformer(changes=[rename_change])
        new_ast_tree = transformer.visit(ast_tree)

        # Convert the new AST back to source code and compare to expected
        new_source_code = ast.unparse(new_ast_tree).strip()
        self.assertEqual(expected_code.strip(), new_source_code)

    def test_variable_rename3(self):
        source_code = """
def example_function():
    count = 10
    counter = count + 1
    print(count, counter)
"""
        expected_code = """
def example_function():
    quantity = 10
    counter = quantity + 1
    print(quantity, counter)
"""

        # Parse the source code into an AST
        ast_tree = ast.parse(source_code)

        # Create a VariableNameChange instance for the rename operation
        rename_change = VariableNameChange(original_name="count", new_name="quantity")

        # Apply the change using the CustomASTTransformer
        transformer = CustomASTTransformer(changes=[rename_change])
        new_ast_tree = transformer.visit(ast_tree)

        # Convert the new AST back to source code and compare to expected
        new_source_code = ast.unparse(new_ast_tree).strip()
        self.assertEqual(expected_code.strip(), new_source_code)


if __name__ == "__main__":
    unittest.main()
