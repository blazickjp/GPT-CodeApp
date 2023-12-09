import unittest
import ast
import astor
from agent.agent_functions.ast_ops import CustomASTTransformer
from agent.agent_functions.file_ops import (
    DeleteClass,
    ModifyFunction,
    DeleteFunction,
    AddClass,
    AddMethod,
    DeleteMethod,
    ModifyClass,
    ModifyMethod,
    AddFunction,
    AddImport,
    DeleteImport,
    VariableNameChange,
    ModifyImport,
)


class TestDocstringModification(unittest.TestCase):
    def test_modify_function_docstring(self):
        source_code = '''
def example_function(param):
    """Original docstring."""
    return param
'''
        expected_docstring = "Updated function docstring."

        modify_function_change = ModifyFunction(
            file_name="test.py",
            function_name="example_function",
            new_docstring=expected_docstring,
        )
        transformer = CustomASTTransformer(changes=[modify_function_change])
        new_ast = transformer.visit(ast.parse(source_code))

        new_docstring = ast.get_docstring(new_ast.body[0])
        self.assertEqual(new_docstring, expected_docstring)

    def test_modify_class_docstring(self):
        source_code = '''
class ExampleClass:
    """Original docstring."""
    pass
'''
        expected_docstring = "Updated class docstring."

        modify_class_change = ModifyClass(
            file_name="test.py",
            class_name="ExampleClass",
            new_docstring=expected_docstring,
        )
        transformer = CustomASTTransformer(changes=[modify_class_change])
        new_ast = transformer.visit(ast.parse(source_code))

        new_docstring = ast.get_docstring(new_ast.body[0])
        self.assertEqual(new_docstring, expected_docstring)

    def test_modify_method_docstring(self):
        print("Starting test_modify_method_docstring")  # Debug print
        source_code = '''
class ExampleClass:
    def example_method(self):
        """Original docstring."""
        pass
    '''
        expected_docstring = "Updated method docstring."

        modify_method_change = ModifyMethod(
            file_name="test.py",
            class_name="ExampleClass",
            method_name="example_method",
            new_docstring=expected_docstring,
        )
        transformer = CustomASTTransformer(changes=[modify_method_change])
        new_ast = transformer.visit(ast.parse(source_code))

        new_docstring = ast.get_docstring(new_ast.body[0].body[0])
        self.assertEqual(new_docstring, expected_docstring)
        print("Finished test_modify_method_docstring")  # Debug print


class TestAddImport(unittest.TestCase):
    def setUp(self):
        self.source_code = """
import pandas as pd
"""

    def test_adding_import_statement(self):
        # Define the import addition
        add_import_change = AddImport(
            file_name="test.py",
            module="math",
            names=None,
            asnames=None,
            objects=["sqrt"],
        )

        self.transformer = CustomASTTransformer(changes=[add_import_change])

        # Parse the source code into an AST
        ast_tree = ast.parse(self.source_code)
        new_ast_tree = self.transformer.visit(ast_tree)
        ast.fix_missing_locations(new_ast_tree)

        # Generate the new source code and define the expected result
        new_source_code = ast.unparse(new_ast_tree).strip()
        print(new_source_code)
        expected_code = "from math import sqrt\nimport pandas as pd"

        # Assert the addition is as expected
        self.assertEqual(expected_code, new_source_code)


class TestDeleteImport(unittest.TestCase):
    def setUp(self):
        self.source_code = "from math import sqrt, sin, cos"
        self.ast_tree = ast.parse(self.source_code)

    def test_removing_import_statement(self):
        # Define the import deletion
        delete_import_change = DeleteImport(
            file_name="test.py", module="math", objects=["sqrt"]
        )
        self.transformer = CustomASTTransformer(changes=[delete_import_change])

        # Apply the change
        new_ast_tree = self.transformer.visit(self.ast_tree)
        ast.fix_missing_locations(new_ast_tree)

        # Generate the new source code and assert it's empty
        new_source_code = ast.unparse(new_ast_tree).strip()
        print(new_source_code)
        self.assertEqual("from math import sin, cos", new_source_code)


class TestModifyImport(unittest.TestCase):
    def setUp(self):
        self.source_code = "from math import sqrt, sin, cos"
        self.ast_tree = ast.parse(self.source_code)

    def test_modifying_import_statement(self):
        # Define the import modification
        modify_import_change = ModifyImport(
            file_name="test.py",
            module="math",
            objects_to_remove=["sqrt"],
            objects_to_add=["acos"],
        )
        self.transformer = CustomASTTransformer(changes=[modify_import_change])

        # Apply the change
        new_ast_tree = self.transformer.visit(self.ast_tree)
        ast.fix_missing_locations(new_ast_tree)

        # Generate the new source code and assert it's empty
        new_source_code = ast.unparse(new_ast_tree).strip()
        print(new_source_code)
        self.assertTrue("acos" in new_source_code)
        self.assertFalse("sqrt" in new_source_code)


class TestModifyClass(unittest.TestCase):
    def setUp(self):
        self.source_code = """
class OldClassName:
    x = 1
    y = 2
"""
        self.ast_tree = ast.parse(self.source_code)

    def test_renaming_class(self):
        # Define the class rename operation
        modify_class_change = ModifyClass(
            file_name="test.py", class_name="OldClassName", new_name="NewClassName"
        )
        self.transformer = CustomASTTransformer(changes=[modify_class_change])

        # Apply the change
        new_ast_tree = self.transformer.visit(self.ast_tree)
        ast.fix_missing_locations(new_ast_tree)

        # Generate the new source code and define the expected result
        new_source_code = ast.unparse(new_ast_tree).strip()
        expected_code = """
class NewClassName:
    x = 1
    y = 2
""".strip()

        # Assert the change is as expected
        self.assertEqual(expected_code, new_source_code)

    def test_modifying_class_attributes(self):
        # TODO: Implement a test for modifying class attributes
        pass


class TestModifyMethod(unittest.TestCase):
    def setUp(self):
        self.source_code = """
class MyClass:
    def method_to_modify(self, x):
        return x + 1
"""
        self.ast_tree = ast.parse(self.source_code)

    def test_modifying_method_body(self):
        # Define the modification
        modify_method_change = ModifyMethod(
            file_name="test.py",
            class_name="MyClass",
            method_name="method_to_modify",
            new_body="return x * 2",
        )

        self.transformer = CustomASTTransformer(changes=[modify_method_change])

        # Apply the modification
        new_ast_tree = self.transformer.visit(self.ast_tree)
        ast.fix_missing_locations(new_ast_tree)

        # Generate the new source code and define the expected result
        new_source_code = ast.unparse(new_ast_tree).strip()
        expected_code = """
class MyClass:

    def method_to_modify(self, x):
        return x * 2
""".strip()

        # Assert the modification is as expected
        self.assertEqual(expected_code, new_source_code)


class TestDeleteMethod(unittest.TestCase):
    def test_deleting_method_from_class(self):
        source_code = """
class MyClass:
    def method_to_delete(self):
        pass

    def should_remain(self):
        pass
"""
        expected_code = """
class MyClass:

    def should_remain(self):
        pass
"""

        # Parse the source code into an AST
        ast_tree = ast.parse(source_code)

        # Create a DeleteMethod instance for the method to be deleted
        delete_method_change = DeleteMethod(
            file_name="test.py", class_name="MyClass", method_name="method_to_delete"
        )

        # Apply the change using the CustomASTTransformer
        transformer = CustomASTTransformer(changes=[delete_method_change])
        new_ast_tree = transformer.visit(ast_tree)
        ast.fix_missing_locations(new_ast_tree)

        # Convert the new AST back to source code and compare to expected
        new_source_code = ast.unparse(new_ast_tree).strip()
        print(new_source_code)
        self.assertEqual(expected_code.strip(), new_source_code)


class TestAddMethod(unittest.TestCase):
    def test_adding_method_to_existing_class(self):
        source_code = """
class MyClass:
    def existing_method(self):
        pass
"""
        expected_code = """
class MyClass:

    def existing_method(self):
        pass

    def new_method(self, arg):
        return arg
"""
        # Parse the source code into an AST
        ast_tree = ast.parse(source_code)

        # Create an AddMethod instance for the new method
        add_method_change = AddMethod(
            file_name="test.py",
            class_name="MyClass",
            method_name="new_method",
            args="self, arg",
            body="return arg",
            decorator_list=[],
            returns=None,
        )

        # Apply the change using the CustomASTTransformer
        transformer = CustomASTTransformer(changes=[add_method_change])
        new_ast_tree = transformer.visit(ast_tree)
        ast.fix_missing_locations(new_ast_tree)

        # Convert the new AST back to source code and compare to expected
        new_source_code = ast.unparse(new_ast_tree).strip()
        print(new_source_code)
        self.assertEqual(expected_code.strip(), new_source_code)


class TestVariableNameChange(unittest.TestCase):
    def test_variable_rename(self):
        source_code = "x = 1"
        expected_code = "y = 1"

        # Parse the source code into an AST
        ast_tree = ast.parse(source_code)

        # Create a VariableNameChange instance for the rename operation
        rename_change = VariableNameChange(
            file_name="test.py", original_name="x", new_name="y"
        )

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
        rename_change = VariableNameChange(
            file_name="test.py", original_name="x", new_name="y"
        )

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
        rename_change = VariableNameChange(
            file_name="test.py", original_name="count", new_name="quantity"
        )

        # Apply the change using the CustomASTTransformer
        transformer = CustomASTTransformer(changes=[rename_change])
        new_ast_tree = transformer.visit(ast_tree)

        # Convert the new AST back to source code and compare to expected
        new_source_code = ast.unparse(new_ast_tree).strip()
        self.assertEqual(expected_code.strip(), new_source_code)


class TestAddFunction(unittest.TestCase):
    def test_adding_simple_function(self):
        source_code = ""
        expected_code = """
def new_function():
    pass
"""

        # Parse the source code into an AST
        ast_tree = ast.parse(source_code)

        # Create an AddFunction instance for the new function
        add_function_change = AddFunction(
            file_name="test.py",
            function_name="new_function",
            args="",
            body="pass",
            decorator_list=[],
            returns=None,
        )

        # Apply the change using the CustomASTTransformer
        transformer = CustomASTTransformer(changes=[add_function_change])
        new_ast_tree = transformer.visit(ast_tree)
        ast.fix_missing_locations(new_ast_tree)

        # Convert the new AST back to source code and compare to expected
        new_source_code = ast.unparse(new_ast_tree).strip()
        print(new_source_code)
        self.assertEqual(expected_code.strip(), new_source_code)


class TestClassMethodChange(unittest.TestCase):
    def test_class_method_rename(self):
        source_code = """
class ExampleClass:
    def method_one(self):
        pass
"""
        expected_code = """
class ExampleClass:

    def renamed_method(self):
        pass
"""

        # Parse the source code into an AST
        ast_tree = ast.parse(source_code)

        # Create a ClassMethodChange instance for the rename operation
        method_change = ModifyMethod(
            file_name="test.py",
            class_name="ExampleClass",
            method_name="method_one",
            new_method_name="renamed_method",
        )

        # Apply the change using the CustomASTTransformer
        transformer = CustomASTTransformer(changes=[method_change])
        new_ast_tree = transformer.visit(ast_tree)

        # Convert the new AST back to source code and compare to expected
        new_source_code = ast.unparse(new_ast_tree).strip()
        self.assertEqual(expected_code.strip(), new_source_code)

    def test_class_method_rename1(self):
        source_code = """
class ExampleClass:
    def method_one(self):
        pass
"""
        expected_code = """
class ExampleClass:

    def method_one(self):
        for i in range(10):
            print(i)
"""

        # Parse the source code into an AST
        ast_tree = ast.parse(source_code)

        # Create a ClassMethodChange instance for the rename operation
        method_change = ModifyMethod(
            file_name="test.py",
            class_name="ExampleClass",
            method_name="method_one",
            new_body="for i in range(10):\n    print(i)",
        )

        # Apply the change using the CustomASTTransformer
        transformer = CustomASTTransformer(changes=[method_change])
        new_ast_tree = transformer.visit(ast_tree)

        # Convert the new AST back to source code and compare to expected
        new_source_code = ast.unparse(new_ast_tree).strip()
        print(new_source_code)
        self.assertEqual(expected_code.strip(), new_source_code)

    def test_class_method_rename2(self):
        source_code = """
class ExampleClass:
    def method_one(self):
        pass
"""
        expected_code = """
class ExampleClass:

    def method_one(self):
        for i in range(10):
            print(i)
        return 'Hello!'
"""

        # Parse the source code into an AST
        ast_tree = ast.parse(source_code)

        # Create a ClassMethodChange instance for the rename operation
        method_change = ModifyMethod(
            file_name="test.py",
            class_name="ExampleClass",
            method_name="method_one",
            new_body="for i in range(10):\n    print(i)\nreturn 'Hello!'",
        )

        # Apply the change using the CustomASTTransformer
        transformer = CustomASTTransformer(changes=[method_change])
        new_ast_tree = transformer.visit(ast_tree)

        # Convert the new AST back to source code and compare to expected
        new_source_code = ast.unparse(new_ast_tree).strip()
        print(new_source_code)
        self.assertEqual(expected_code.strip(), new_source_code)


class TestDeleteClass(unittest.TestCase):
    def test_deleting_class(self):
        source_code = """
class ClassToDelete:
    def method(self):
        pass

class AnotherClass:
    def method(self):
        pass
"""
        expected_code = """
class AnotherClass:

    def method(self):
        pass
"""
        delete_class_change = DeleteClass(
            file_name="test.py", class_name="ClassToDelete"
        )
        transformer = CustomASTTransformer(changes=[delete_class_change])
        new_ast = transformer.visit(ast.parse(source_code))
        new_code = ast.unparse(new_ast).strip()
        print(new_code)
        self.assertEqual(expected_code.strip(), new_code)


class TestModifyFunction(unittest.TestCase):
    def test_modifying_function(self):
        source_code = """
def function_to_modify():
    return 1
"""
        expected_code = """
def modified_function():
    return 2
"""
        modify_function_change = ModifyFunction(
            file_name="test.py",
            function_name="function_to_modify",
            new_name="modified_function",
            new_body="  return 2",
        )
        transformer = CustomASTTransformer(changes=[modify_function_change])
        new_ast = transformer.visit(ast.parse(source_code))
        new_code = ast.unparse(new_ast).strip()

        self.assertEqual(expected_code.strip(), new_code)


class TestDeleteFunction(unittest.TestCase):
    def test_deleting_function(self):
        source_code = """
def function_to_delete():
    pass

def function_to_keep():
    pass
"""
        expected_code = """
def function_to_keep():
    pass
"""
        delete_function_change = DeleteFunction(
            file_name="test.py", function_name="function_to_delete"
        )
        transformer = CustomASTTransformer(changes=[delete_function_change])
        new_ast = transformer.visit(ast.parse(source_code))
        new_code = ast.unparse(new_ast).strip()
        print(new_code)

        self.assertEqual(expected_code.strip(), new_code)


if __name__ == "__main__":
    unittest.main()
