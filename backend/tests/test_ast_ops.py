import unittest
import ast
import astor
import textwrap
from agent.agent_functions.ast_ops import (
    ASTChangeApplicator,
    AddFunction,
    DeleteFunction,
    ModifyFunction,
    ModifyClass,
    CustomASTTransformer,
    AddClass,
)


class TestASTOps(unittest.TestCase):
    def test_add_function(self):
        source_code = "def existing_function():\n    pass\n"
        add_function_op = AddFunction(
            file_name="example.py",
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
        source_code = (
            "\ndef function_to_delete():\n    pass\n\ndef keep_me():\n    pass\n"
        )
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

    def test_modify_class(self):
        source_code = "\nclass MyClass:\n    x = 1\n"
        expected_code = "\nclass MyClass:\n    x = 2\n"
        modify_class_change = ModifyClass(
            file_name="test.py", class_name="MyClass", new_body="x = 2"
        )
        transformer = CustomASTTransformer(changes=[modify_class_change])
        new_ast = transformer.visit(ast.parse(source_code))
        new_code = astor.to_source(new_ast).strip()
        print(f"new_code: {new_code}")
        self.assertEqual(expected_code.strip(), new_code)

    def test_adding_multiple_decorators(self):
        add_func = AddFunction(
            file_name="test.py",
            function_name="decorated_function",
            args="arg1, arg2",
            body="print(arg1, arg2)",
            decorator_list=["decorator_one", "decorator_two(arg2)"],
            returns=None,
        )
        transformer = CustomASTTransformer([])
        func_node = transformer.create_function_node(add_func)
        self.assertEqual(len(func_node.decorator_list), 2)
        self.assertEqual(func_node.decorator_list[0].id, "decorator_one")
        self.assertEqual(func_node.decorator_list[1].func.id, "decorator_two")
        self.assertEqual(func_node.decorator_list[1].args[0].id, "arg2")

    def test_adding_class_with_method(self):
        source_code = ""
        expected_code = textwrap.dedent(
            """
        class NewClass:

            def new_method(self):
                pass
        """
        ).lstrip("\n")
        add_class_change = AddClass(
            file_name="test.py",
            class_name="NewClass",
            body="""def new_method(self):
    pass""",
        )
        applicator = ASTChangeApplicator(source_code)
        modified_code = applicator.apply_changes([add_class_change])
        self.assertEqual(expected_code.strip(), modified_code.strip())


class TestASTOps2(unittest.TestCase):
    def test_create_function_node_with_decorator(self):
        add_func = AddFunction(
            file_name="test.py",
            function_name="hello_world",
            args="",
            body="return 'Hello, World!'",
            decorator_list=["app.get('/hello-world')"],
            returns="str",
        )
        transformer = CustomASTTransformer([])
        func_node = transformer.create_function_node(add_func)
        self.assertEqual(len(func_node.decorator_list), 1)
        self.assertIsInstance(func_node.decorator_list[0], ast.Call)
        self.assertEqual(func_node.decorator_list[0].func.attr, "get")
        self.assertEqual(func_node.decorator_list[0].func.value.id, "app")
        self.assertEqual(func_node.decorator_list[0].args[0].s, "/hello-world")
        self.assertEqual(func_node.name, "hello_world")
        self.assertEqual(len(func_node.body), 1)
        self.assertIsInstance(func_node.body[0], ast.Return)
        self.assertEqual(func_node.body[0].value.s, "Hello, World!")


class TestAddClass(unittest.TestCase):
    def test_add_function_with_default_args(self):
        source_code = ""
        add_function_op = AddFunction(
            file_name="example.py",
            function_name="function_with_defaults",
            args="a=1, b=2",
            body="return a + b",
            decorator_list=[],
            returns=None,
        )
        applicator = ASTChangeApplicator(source_code)
        modified_code = applicator.apply_changes([add_function_op])
        self.assertIn("def function_with_defaults(a=1, b=2):", modified_code)
        self.assertIn("return a + b", modified_code)

    def test_add_function_with_default_args_and_bad_indent(self):
        source_code = ""
        add_function_op = AddFunction(
            file_name="example.py",
            function_name="function_with_defaults",
            args="a=1, b=2",
            body="  return a + b",
            decorator_list=[],
            returns=None,
        )
        applicator = ASTChangeApplicator(source_code)
        modified_code = applicator.apply_changes([add_function_op])
        self.assertIn("def function_with_defaults(a=1, b=2):", modified_code)
        self.assertIn("return a + b", modified_code)

    def test_adding_class_with_method_and_correct_indentation(self):
        source_code = ""
        expected_code = textwrap.dedent(
            "class NewClass:\n\n    def new_method(self):\n        pass\n"
        )
        add_class_change = AddClass(
            file_name="test.py",
            class_name="NewClass",
            body="""def new_method(self):
        pass""",
        )
        applicator = ASTChangeApplicator(source_code)
        modified_code = applicator.apply_changes([add_class_change])
        self.assertEqual(expected_code.strip(), modified_code.strip())

    def test_adding_new_class(self):
        source_code = ""
        expected_code = (
            "\nclass NewClass:\n\n    def new_method(self):\n        pass\n    ".strip()
        )
        add_class_change = AddClass(
            file_name="test.py",
            class_name="NewClass",
            body="""def new_method(self):
    pass""",
        )
        transformer = CustomASTTransformer(changes=[add_class_change])
        new_ast = transformer.visit(ast.parse(source_code))
        new_code = astor.to_source(new_ast).strip()
        print(new_code)
        self.assertEqual(expected_code, new_code)


if __name__ == "__main__":
    unittest.main()
