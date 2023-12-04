import ast
import difflib
import astor
from typing import List
import textwrap  # Import textwrap at the top of your file
from pathlib import Path

from agent.agent_functions.file_ops import (
    AddFunction,
    DeleteFunction,
    ModifyFunction,
    AddClass,
    DeleteClass,
    ModifyClass,
    AddMethod,
    DeleteMethod,
    ModifyMethod,
    VariableNameChange,
    AddImport,
    DeleteImport,
    ModifyImport,
)

ASTNode = ast.AST


def adjust_indentation(code, level=4):
    # Split the code into lines
    lines = code.splitlines()

    # Strip leading whitespace using textwrap.dedent but preserve internal indentation
    dedented_text = textwrap.dedent("\n".join(lines))

    # Re-indent the code with the specified number of spaces
    indented_text = textwrap.indent(dedented_text, " " * level)

    # Return the re-indented code
    return indented_text


class ASTChangeApplicator:
    """
    Class responsible for applying changes to an Abstract Syntax Tree (AST) based on a list of change operations.
    """

    def __init__(self, source_code: str):
        self.source_code = source_code
        self.ast_tree = ast.parse(source_code)
        self.changes = []

    def apply_changes(self, changes):
        # First, we sort the changes.

        self.sorted_changes = self.sort_changes(changes)

        # Then, we apply the changes to the AST.
        transformer = CustomASTTransformer(self.sorted_changes)
        for change in self.sorted_changes:
            transformer.change = change
            self.ast_tree = transformer.visit(self.ast_tree)

        # Finally, we return the modified source code.
        modified_source = astor.to_source(self.ast_tree)
        print("Modified AST:", ast.dump(self.ast_tree, indent=4))  # Diagnostic output
        print("Modified Source Code:\n", modified_source)  # Diagnostic output

        return astor.to_source(self.ast_tree)

    def sort_changes(self, changes):
        # A simple sorting strategy: deletions, then modifications, then additions.
        # This should be refined based on your specific use case.
        deletion_types = (DeleteFunction, DeleteClass, DeleteMethod, DeleteImport)
        modification_types = (
            ModifyFunction,
            ModifyClass,
            ModifyMethod,
            ModifyImport,
            VariableNameChange,
        )
        addition_types = (AddFunction, AddClass, AddMethod, AddImport)

        deletions = [change for change in changes if isinstance(change, deletion_types)]
        modifications = [
            change for change in changes if isinstance(change, modification_types)
        ]
        additions = [change for change in changes if isinstance(change, addition_types)]

        # Now, we concatenate the lists to get the final order of changes.
        sorted_changes = deletions + modifications + additions
        return sorted_changes


class CustomASTTransformer(ast.NodeTransformer):
    """
    Custom AST transformer for applying changes to an AST.
    """

    def __init__(self, changes: List[ASTNode]) -> None:
        self.changes: List[ASTNode] = changes
        super().__init__()

    def visit_Module(self, node):
        # Handle adding new classes and functions to the module
        for change in self.changes:
            if isinstance(change, AddFunction):
                # Continue with the rest of the process
                new_function_node = self.create_function_node(change)
                node.body.append(new_function_node)
            elif isinstance(change, DeleteFunction):
                node.body = [
                    n
                    for n in node.body
                    if not (
                        isinstance(n, ast.FunctionDef)
                        and n.name == change.function_name
                    )
                ]
            elif isinstance(change, AddClass):
                new_class_node = self.create_class_node(change)
                node.body.append(new_class_node)
            elif isinstance(change, DeleteClass):
                node.body = [
                    n
                    for n in node.body
                    if not (isinstance(n, ast.ClassDef) and n.name == change.class_name)
                ]
            elif isinstance(change, AddImport):
                new_import_node = self.create_import_node(change)
                node.body.insert(0, new_import_node)
            elif isinstance(change, DeleteImport):
                node.body = self.remove_import_node(node.body, change)
            elif isinstance(change, ModifyImport):
                node.body = self.modify_import_node(node.body, change)

        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node):
        # Handle renaming, adding, deleting, and modifying methods in a class
        for change in self.changes:
            if isinstance(change, ModifyClass) and node.name == change.class_name:
                if change.new_name is not None:
                    node.name = change.new_name
                if change.new_docstring is not None:
                    node.body.insert(0, ast.Expr(value=ast.Str(s=change.new_docstring)))
                if change.new_bases is not None:
                    node.bases = [
                        ast.parse(base).body[0].value for base in change.new_bases
                    ]
                if change.new_body is not None:
                    new_body_ast = ast.parse(change.new_body).body
                    node.body = new_body_ast
                if change.new_decorator_list is not None:
                    node.decorator_list = [
                        ast.parse(deco).body[0].value
                        for deco in change.new_decorator_list
                    ]
                if change.new_args is not None:
                    node.args = self.create_args(change.new_args)

            elif isinstance(change, AddMethod) and node.name == change.class_name:
                new_method_node = self.create_method_node(change)
                node.body.append(new_method_node)
            elif isinstance(change, DeleteMethod) and node.name == change.class_name:
                node.body = [
                    n
                    for n in node.body
                    if not (
                        isinstance(n, ast.FunctionDef) and n.name == change.method_name
                    )
                ]
            elif isinstance(change, ModifyMethod) and node.name == change.class_name:
                for n in node.body:
                    if isinstance(n, ast.FunctionDef) and n.name == change.method_name:
                        if change.new_args is not None:
                            n.args = self.create_args(change.new_args)
                        if change.new_body is not None:
                            new_body_ast = ast.parse(change.new_body).body
                            n.body = new_body_ast
                        if change.new_method_name is not None:
                            n.name = change.new_method_name
                        if change.new_docstring is not None:
                            # Assuming the first node in the body is the docstring
                            docstring_node = ast.get_docstring(n)
                            if docstring_node is not None:
                                # Replace the existing docstring
                                n.body[0].value = ast.Str(s=change.new_docstring)
                            else:
                                # Insert a new docstring at the beginning of the function body
                                n.body.insert(
                                    0, ast.Expr(value=ast.Str(s=change.new_docstring))
                                )

        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):
        # Handle renaming and modifying functions at the module level
        for change in self.changes:
            if isinstance(change, ModifyFunction) and node.name == change.function_name:
                if change.new_args is not None:
                    node.args = self.create_args(change.new_args)
                if change.new_body is not None:
                    unindented_body = textwrap.dedent(change.new_body.lstrip("\n"))
                    node.body = [ast.parse(unindented_body).body[0]]
                if change.new_name is not None:
                    node.name = change.new_name
                if change.new_docstring is not None:
                    node.body.insert(0, ast.Expr(value=ast.Str(s=change.new_docstring)))

        self.generic_visit(node)
        return node

    def visit_Name(self, node):
        # Handle variable name changes
        for change in self.changes:
            if (
                isinstance(change, VariableNameChange)
                and node.id == change.original_name
            ):
                node.id = change.new_name
        self.generic_visit(node)
        return node

    # Helper methods
    def create_function_node(self, change):
        # Remove the leading indentation from the body if necessary
        unindented_body = textwrap.dedent(change.body.lstrip("\n"))
        body_ast = ast.parse(unindented_body).body

        # Ensure we have a properly formatted body (list of statements)
        if len(body_ast) == 1 and isinstance(body_ast[0], ast.Expr):
            body_ast = [ast.Return(value=body_ast[0].value)]

        # Parse decorators in the context of a dummy function to get the correct ast nodes
        decorator_nodes = []
        for decorator in change.decorator_list:
            # Ensure the decorator is properly prefixed and in its own dummy function definition
            fake_func_def = f"@{decorator.strip()}\ndef _func():\n    pass\n"
            try:
                decorator_node = ast.parse(fake_func_def).body[0].decorator_list[0]
                decorator_nodes.append(decorator_node)
            except IndexError:
                raise ValueError(f"Invalid decorator syntax: {decorator}")

        return ast.FunctionDef(
            name=change.function_name,
            args=self.create_args(change.args),
            body=body_ast,
            decorator_list=decorator_nodes,
            returns=ast.parse(change.returns).body[0].value if change.returns else None,
        )

    def create_class_node(self, change):
        unindented_body = textwrap.dedent(change.body.lstrip("\n"))

        class_body = (
            [ast.parse(unindented_body).body[0]]
            if isinstance(unindented_body, str)
            else unindented_body
        )
        bases = [ast.parse(base).body[0].value for base in change.bases]
        decorator_list = [
            ast.parse(deco).body[0].value for deco in change.decorator_list
        ]

        # Handling Python 3.11 compatibility where `keywords` attribute may not be present
        class_def_args = {
            "name": change.class_name,
            "bases": bases,
            "body": class_body,
            "decorator_list": decorator_list,
        }

        # Include keywords if it's a valid attribute for the current Python version
        if hasattr(ast.ClassDef, "keywords"):
            class_def_args["keywords"] = []

        return ast.ClassDef(**class_def_args)

    def create_method_node(self, change):
        unindented_body = textwrap.dedent(change.body.lstrip("\n"))
        return ast.FunctionDef(
            name=change.method_name,
            args=self.create_args(change.args),
            body=[ast.parse(unindented_body).body[0]],
            decorator_list=[ast.parse(d).body[0].value for d in change.decorator_list],
            returns=ast.parse(change.returns).body[0].value if change.returns else None,
        )

    def create_args(self, args_str):
        return ast.parse("def _({}): pass".format(args_str)).body[0].args

    # Helper method to create import node
    def create_import_node(self, add_import):
        if add_import.names:
            return ast.Import(
                names=[ast.alias(name=name, asname=None) for name in add_import.names]
            )
        elif add_import.objects:
            return ast.ImportFrom(
                module=add_import.module,
                names=[ast.alias(name=obj, asname=None) for obj in add_import.objects],
                level=0,
            )
        else:
            return ast.Import(names=[ast.alias(name=add_import.module, asname=None)])

    # Helper method to remove import node
    def remove_import_node(self, body, delete_import):
        new_body = []
        for node in body:
            if isinstance(node, ast.ImportFrom) and node.module == delete_import.module:
                # Keep only names not in delete_import.objects
                new_names = [
                    alias
                    for alias in node.names
                    if alias.name not in delete_import.objects
                ]
                if new_names:
                    # Create a new node with the remaining names
                    new_node = ast.ImportFrom(
                        module=node.module, names=new_names, level=node.level
                    )
                    new_body.append(new_node)
            else:
                new_body.append(node)
        return new_body

    # Helper method to modify import node
    def modify_import_node(self, body, modify_import):
        new_body = []
        for node in body:
            if isinstance(node, ast.ImportFrom) and node.module == modify_import.module:
                # Keep only names not in modify_import.objects
                new_names = [
                    alias
                    for alias in node.names
                    if alias.name not in modify_import.objects_to_remove
                ]
                print([alias.name for alias in node.names])
                new_names.extend(
                    [
                        ast.alias(name=obj, asname=None)
                        for obj in modify_import.objects_to_add
                    ]
                )
                print(modify_import.objects_to_add)
                print(modify_import.objects_to_remove)
                print([alias.name for alias in node.names])
                if new_names:
                    # Create a new node with the remaining names
                    new_node = ast.ImportFrom(
                        module=node.module, names=new_names, level=node.level
                    )
                    new_body.append(new_node)
            else:
                new_body.append(node)
        return new_body
