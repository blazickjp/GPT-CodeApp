import ast
import json
import astor
import difflib
from instructor import OpenAISchema
from pydantic import Field


def from_streaming_response(completion, class_list):
    function_name = None
    json_accumulator = ""
    idx = None

    for _, chunk in enumerate(completion):
        if chunk.choices:
            delta = chunk.choices[0].delta
            if delta.tool_calls:
                for call in delta.tool_calls:
                    # If we've started a new call, reset the accumulator and save the function name
                    if call.index != idx:
                        if json_accumulator:
                            try:
                                data = json.loads(json_accumulator)
                                if function_name in class_list:
                                    yield class_list[function_name](**data)
                            except json.JSONDecodeError as e:
                                print(f"JSON decode error: {e}")

                        function_name = call.function.name
                        json_accumulator = ""
                        idx = call.index

                    # Accumulate JSON string
                    json_accumulator += call.function.arguments

    # After the loop, process the last accumulated JSON
    if json_accumulator:
        try:
            data = json.loads(json_accumulator)
            if function_name in class_list:
                yield class_list[function_name](**data)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")


class Changes(OpenAISchema):
    """
    A class representing a list of operations that can be performed on a file.

    Attributes:
        ops Tuple(TaskType, Op): A list of operations that can be performed on a file.

    Usage:
    """

    def execute(self):
        """
        Execute all the operations in the list of operations.

        Returns:
            str: The new source code after all the operations have been executed.
        """
        for op in self.ops:
            with open(op.file_path, "r") as f:
                source_code = f.read()

            self.files.add((op.file_path, source_code))

            # Apply changes to the source code
            applicator = ASTChangeApplicator(source_code)
            source_code = applicator.apply_changes(op.changes)

            with open(op.file_path, "w") as f:
                f.write(source_code)

            diff = self.diff(source_code)
            self.diffs.append(diff)

        return self.diffs

    def diff(self, new_source_code):
        """
        Generates a diff from the original source code using difflib
        """
        return difflib.unified_diff(
            self.source_code.splitlines(), new_source_code.splitlines()
        )


class ASTChangeApplicator:
    def __init__(self, source_code: str):
        self.source_code = source_code
        self.ast_tree = ast.parse(source_code)

    def apply_changes(self, changes):
        transformer = CustomASTTransformer(changes)
        modified_tree = transformer.visit(self.ast_tree)
        return astor.to_source(modified_tree)

    def check_and_apply_changes(self, changes):
        # Here we would sort and check for conflicts.
        sorted_changes = self.sort_changes(changes)
        for change in sorted_changes:
            if not self.is_conflict(change):
                self.apply_changes(change)
        return astor.to_source(self.ast_tree)

    def generate_diff(self, new_source_code):
        """
        Generates a diff from the original source code using difflib
        """
        return difflib.unified_diff(
            self.source_code.splitlines(), new_source_code.splitlines()
        )

    def is_conflict(self, change):
        return NotImplementedError

    def sort_changes(self, changes):
        return NotImplementedError


class CustomASTTransformer(ast.NodeTransformer):
    def __init__(self, changes):
        self.changes = changes
        super().__init__()

    def visit_Module(self, node):
        # Handle adding new classes and functions to the module
        for change in self.changes:
            if isinstance(change, AddFunction):
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

        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node):
        # Handle renaming, adding, deleting, and modifying methods in a class
        for change in self.changes:
            if isinstance(change, ModifyClass) and node.name == change.class_name:
                if change.new_name is not None:
                    node.name = change.new_name
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

        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):
        # Handle renaming and modifying functions at the module level
        for change in self.changes:
            if isinstance(change, ModifyFunction) and node.name == change.function_name:
                if change.new_args is not None:
                    node.args = self.create_args(change.new_args)
                if change.new_body is not None:
                    node.body = [ast.parse(change.new_body).body[0]]
                if change.new_name is not None:
                    node.name = change.new_name
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
        return ast.FunctionDef(
            name=change.function_name,
            args=self.create_args(change.args),
            body=[ast.parse(change.body).body[0]],
            decorator_list=[ast.parse(d).body[0].value for d in change.decorator_list],
            returns=ast.parse(change.returns).body[0].value if change.returns else None,
        )

    def create_class_node(self, change):
        class_body = (
            [ast.parse(change.body).body[0]]
            if isinstance(change.body, str)
            else change.body
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
        return ast.FunctionDef(
            name=change.method_name,
            args=self.create_args(change.args),
            body=[ast.parse(change.body).body[0]],
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


class AddFunction(Changes):
    """
    Represents a function to be added to a Python file.
    """

    file_name: str = Field(
        ..., description="The name of the file to add the function to."
    )
    function_name: str = Field(..., description="The name of the function.")
    args: str = Field(..., description="The arguments of the function.")
    body: str = Field(..., description="The body of the function.")
    decorator_list: list[str] = Field(
        [], description="The list of decorators to be applied to the function."
    )
    returns: str | None = Field(None, description="The return type of the function.")

    def to_string(self):
        out = dict(
            file_name=self.file_name,
            function_name=self.function_name,
            args=self.args,
            body=self.body,
            decorator_list=self.decorator_list,
            returns=self.returns,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


class DeleteFunction(Changes):
    """
    Represents a request to delete a function from the agent.
    """

    file_name: str = Field(
        ..., description="The name of the file containing the function to delete."
    )
    function_name: str = Field(..., description="The name of the function to delete.")

    def to_string(self):
        out = dict(
            file_name=self.file_name,
            function_name=self.function_name,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


class ModifyFunction(Changes):
    """
    A class representing modifications to a function.
    """

    file_name: str = Field(
        ..., description="The name of the file containing the function to modify."
    )
    function_name: str = Field(..., description="The name of the function to modify.")
    new_args: str | None = Field(
        None, description="The new arguments for the function."
    )
    new_body: str | None = Field(None, description="The new body of the function.")
    new_decorator_list: list[str] | None = Field(
        None, description="The new list of decorators for the function."
    )
    new_returns: str | None = Field(
        None, description="The new return type for the function."
    )
    new_name: str | None = Field(None, description="The new name for the function.")

    def to_string(self):
        out = dict(
            file_name=self.file_name,
            function_name=self.function_name,
            new_args=self.new_args,
            new_body=self.new_body,
            new_decorator_list=self.new_decorator_list,
            new_returns=self.new_returns,
            new_name=self.new_name,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


class AddClass(Changes):
    """Represents a class to be added to a file."""

    file_name: str = Field(..., description="The name of the file to add the class to.")
    class_name: str = Field(..., description="The name of the class.")
    bases: list[str] = Field([], description="The base classes for the class.")
    body: str = Field(..., description="The body of the class.")
    decorator_list: list[str] = Field(
        [], description="The list of decorators to be applied to the class."
    )

    def to_string(self):
        out = dict(
            file_name=self.file_name,
            class_name=self.class_name,
            bases=self.bases,
            body=self.body,
            decorator_list=self.decorator_list,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


class DeleteClass(Changes):
    """Represents a class to be deleted.

    Attributes:
        file_name (str): The name of the file containing the class to be deleted.
        class_name (str): The name of the class to be deleted.
    """

    file_name: str = Field(
        ..., description="The name of the file containing the class to delete."
    )
    class_name: str = Field(..., description="The name of the class to delete.")


class ModifyClass(Changes):
    """Represents a request to modify a Python class."""

    file_name: str = Field(
        ..., description="The name of the file containing the class to modify."
    )
    class_name: str = Field(..., description="The name of the class to modify.")
    new_bases: list[str] | None = Field(
        None, description="The new base classes for the class."
    )
    new_body: list | None = Field(None, description="The new body of the class.")
    new_decorator_list: list[str] | None = Field(
        None, description="The new list of decorators for the class."
    )
    new_name: str | None = Field(None, description="The new name for the class.")
    new_args: str | None = Field(None, description="The new arguments for the class.")

    def to_string(self):
        out = dict(
            file_name=self.file_name,
            class_name=self.class_name,
            new_bases=self.new_bases,
            new_body=self.new_body,
            new_decorator_list=self.new_decorator_list,
            new_name=self.new_name,
            new_args=self.new_args,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


class AddMethod(Changes):
    """
    Represents a method to be added to a class.
    """

    file_name: str = Field(
        ...,
        description="The name of the file containing the class to add the method to.",
    )
    class_name: str = Field(
        ..., description="The name of the class to add the method to."
    )
    method_name: str = Field(..., description="The name of the method.")
    args: str = Field(..., description="The arguments of the method.")
    body: str = Field(..., description="The body of the method.")
    decorator_list: list[str] = Field(
        [], description="The list of decorators to be applied to the method."
    )
    returns: str | None = Field(None, description="The return type of the method.")

    def to_string(self):
        out = dict(
            file_name=self.file_name,
            class_name=self.class_name,
            method_name=self.method_name,
            args=self.args,
            body=self.body,
            decorator_list=self.decorator_list,
            returns=self.returns,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


class DeleteMethod(Changes):
    """Represents a method to be deleted from a class."""

    file_name: str = Field(
        ...,
        description="The name of the file containing the class to delete the method from.",
    )

    class_name: str = Field(
        ..., description="The name of the class to delete the method from."
    )
    method_name: str = Field(..., description="The name of the method to delete.")

    def to_string(self):
        out = dict(
            file_name=self.file_name,
            class_name=self.class_name,
            method_name=self.method_name,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


class ModifyMethod(Changes):
    """Represents a method modification operation."""

    file_name: str = Field(
        ...,
        description="The name of the file containing the class to modify the method in.",
    )
    class_name: str = Field(
        ..., description="The name of the class to modify the method in."
    )
    method_name: str = Field(..., description="The name of the method to modify.")
    new_args: str | None = Field(None, description="The new arguments for the method.")
    new_body: str | None = Field(None, description="The new body of the method.")
    new_decorator_list: list[str] | None = Field(
        None, description="The new list of decorators for the method."
    )
    new_method_name: str | None = Field(
        None, description="The new name for the method."
    )
    new_returns: str | None = Field(
        None, description="The new return type for the method."
    )

    def to_string(self):
        out = dict(
            file_name=self.file_name,
            class_name=self.class_name,
            method_name=self.method_name,
            new_args=self.new_args,
            new_body=self.new_body,
            new_decorator_list=self.new_decorator_list,
            new_method_name=self.new_method_name,
            new_returns=self.new_returns,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


class VariableNameChange(Changes):
    """
    Represents a request to change the name of a variable. Changes take place over the entire codebase.
    """

    original_name: str = Field(..., description="The original name of the variable.")
    new_name: str = Field(..., description="The new name of the variable.")

    def to_string(self):
        out = dict(original_name=self.original_name, new_name=self.new_name)
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


class AddImport(Changes):
    """
    Represents an import statement to be added to a Python file.
    """

    file_name: str = Field(
        ..., description="The name of the file to add the import to."
    )
    module: str = Field(..., description="The name of the module to import.")
    names: list | None = Field(
        None, description="The names to import from the module. Defaults to None."
    )
    asnames: list | None = Field(
        None, description="The names to import from the module with an alias."
    )
    objects: list | None = Field(
        None, description="The objects to import from the module."
    )

    def to_string(self):
        out = dict(
            file_name=self.file_name,
            module=self.module,
            names=self.names,
            asnames=self.asnames,
            objects=self.objects,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


class DeleteImport(Changes):
    """
    Represents a request to delete one or more imports from a Python module.
    """

    file_name: str = Field(
        ..., description="The name of the file to delete the import from."
    )
    module: str = Field(
        ..., description="The name of the module to delete imports from."
    )
    names: list | None = Field(
        None, description="The names to delete from the module. Defaults to None."
    )
    asnames: list | None = Field(
        None, description="The names to delete from the module with an alias."
    )
    objects: list | None = Field(
        None, description="The objects to delete from the module."
    )

    def to_string(self):
        out = dict(
            file_name=self.file_name,
            module=self.module,
            names=self.names,
            asnames=self.asnames,
            objects=self.objects,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


class ModifyImport(Changes):
    """
    Represents a modification to an import statement in a Python file."""

    file_name: str = Field(
        ..., description="The name of the file containing the import to modify."
    )
    module: str = Field(..., description="The name of the module to modify.")
    new_names: list | None = Field(
        None, description="The new names to import from the module."
    )
    new_asnames: list | None = Field(
        None, description="The new names to import from the module with an alias."
    )
    new_objects: list | None = Field(None, description="The new objects to import.")

    def to_string(self):
        out = dict(
            file_name=self.file_name,
            module=self.module,
            new_names=self.new_names,
            new_asnames=self.new_asnames,
            new_objects=self.new_objects,
        )
        return "\n\n```json\n" + json.dumps(out) + "\n```\n"


_OP_LIST = [
    AddImport,
    DeleteImport,
    AddFunction,
    DeleteFunction,
    AddClass,
    DeleteClass,
    AddMethod,
    DeleteMethod,
    ModifyFunction,
    ModifyClass,
    ModifyMethod,
    ModifyImport,
    VariableNameChange,
]

_OP_LIST = {cls.__name__: cls for cls in _OP_LIST}
