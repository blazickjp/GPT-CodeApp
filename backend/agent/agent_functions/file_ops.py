import ast
import json
import astor
import difflib
from instructor import OpenAISchema


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

    # @classmethod
    # def from_streaming_response(cls, completion):
    #     name, json_chunks = cls.extract_json(completion)
    #     yield from cls.tasks_from_chunks(json_chunks, name)

    # @classmethod
    # def tasks_from_chunks(cls, json_chunks, name):
    #     potential_object = ""
    #     for chunk in json_chunks:
    #         potential_object += chunk
    #         if potential_object.strip():  # Ensure the string is not just whitespace
    #             try:
    #                 # Convert the JSON string to a dictionary
    #                 potential_dict = json.loads(potential_object)
    #                 # Now you can unpack the dictionary with **
    #                 yield cls(**potential_dict)
    #                 potential_object = (
    #                     ""  # Reset potential_object after successful yield
    #                 )
    #             except json.JSONDecodeError:
    #                 # Handle incomplete JSON by waiting for more chunks
    #                 continue

    # @staticmethod
    # def extract_json(completion):
    #     NAME = None
    #     for idx, chunk in enumerate(completion):
    #         if chunk.choices:
    #             delta = chunk.choices[0].delta
    #             if delta.tool_calls:
    #                 NAME = (
    #                     delta.tool_calls[0].function.name
    #                     if delta.tool_calls[0].function.name
    #                     else NAME
    #                 )
    #                 if delta.tool_calls[0].function.arguments:
    #                     yield NAME, delta.tool_calls[0].function.arguments

    # @staticmethod
    # def get_object(str, stack):
    #     for i, c in enumerate(str):
    #         if c == "{":
    #             stack += 1
    #             first = i
    #         if c == "}" and stack > 0:
    #             stack -= 1
    #             if stack == 0:
    #                 return True, str[first + 1 : i]
    #     return None, str


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
                self.apply_change(change)
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

    Args:
        file_name (str): The name of the file to add the function to.
        function_name (str): The name of the function.
        args (str): The arguments of the function.
        body (str): The body of the function.
        decorator_list (list[str], optional): The list of decorators applied to the function. Defaults to [].
        returns (str | None, optional): The return type of the function. Defaults to None.
    """

    file_name: str
    function_name: str
    args: str
    body: str
    decorator_list: list[str] = []
    returns: str | None = None


class DeleteFunction(Changes):
    """
    Represents a request to delete a function from the agent.

    Attributes:
        file_name (str): The name of the file containing the function to delete.
        function_name (str): The name of the function to delete.
    """

    file_name: str
    function_name: str


class ModifyFunction(Changes):
    """
    A class representing modifications to a function.

    Attributes:
        file_name (str): The name of the file containing the function to modify.
        function_name (str): The name of the function to modify.
        new_args (str | None): The new arguments for the function, if any.
        new_body (str | None): The new body of the function, if any.
        new_decorator_list (list[str] | None): The new list of decorators for the function, if any.
        new_returns (str | None): The new return type for the function, if any.
        new_name (str | None): The new name for the function, if any.
    """

    file_name: str
    function_name: str
    new_args: str | None = None
    new_body: str | None = None
    new_decorator_list: list[str] | None = None
    new_returns: str | None = None
    new_name: str | None = None


class AddClass(Changes):
    """Represents a class to be added to a file.

    Attributes:
        file_name (str): The name of the file to add the class to.
        class_name (str): The name of the class.
        bases (list[str], optional): The base classes of the class. Defaults to an empty list.
        body (str): The body of the class.
        decorator_list (list[str], optional): The decorators applied to the class. Defaults to an empty list.
    """

    file_name: str
    class_name: str
    bases: list[str] = []
    body: str
    decorator_list: list[str] = []


class DeleteClass(Changes):
    """Represents a class to be deleted.

    Attributes:
        file_name (str): The name of the file containing the class to be deleted.
        class_name (str): The name of the class to be deleted.
    """

    file_name: str
    class_name: str


class ModifyClass(Changes):
    """Represents a request to modify a Python class.

    Attributes:
        file_name (str): The name of the file containing the class to modify.
        name (str): The name of the class to modify.
        new_bases (list[str], optional): The new base classes for the class.
        new_body (list, optional): The new body of the class, which might include
            method definitions, etc.
        new_decorator_list (list[str], optional): The new decorators for the class.
        new_name (str, optional): The new name for the class.
    """

    file_name: str
    class_name: str
    new_bases: list[str] | None = None
    new_body: list | None = None
    new_decorator_list: list[str] | None = None
    new_name: str | None = None
    new_args: str | None = None


class AddMethod(Changes):
    """
    Represents a method to be added to a class.

    Attributes:
        file_name (str): The name of the file containing the class to which the method will be added.
        class_name (str): The name of the class to which the method will be added.
        method_name (str): The name of the method.
        args (str): The arguments of the method.
        body (str): The body of the method.
        decorator_list (list[str], optional): The list of decorators to be applied to the method. Defaults to [].
        returns (str, optional): The return type of the method. Defaults to None.
    """

    file_name: str
    class_name: str
    method_name: str
    args: str
    body: str
    decorator_list: list[str] = []
    returns: str | None = None


class DeleteMethod(Changes):
    """Represents a method to be deleted from a class.

    Attributes:
        file_name (str): The name of the file containing the class.
        class_name (str): The name of the class containing the method.
        method_name (str): The name of the method to be deleted.
    """

    file_name: str
    class_name: str
    method_name: str


class ModifyMethod(Changes):
    """Represents a method modification operation.

    Attributes:
        file_name (str): The name of the file containing the class.
        class_name (str): The name of the class containing the method to be modified.
        method_name (str): The name of the method to be modified.
        new_args (str, optional): The new arguments for the method. Defaults to None.
        new_body (str, optional): The new body of the method. Defaults to None.
        new_decorator_list (list[str], optional): The new list of decorators for the method. Defaults to None.
        new_method_name (str, optional): The new name for the method. Defaults to None.
        new_returns (str, optional): The new return type for the method. Defaults to None.
    """

    file_name: str
    class_name: str
    method_name: str
    new_args: str | None = None
    new_body: str | None = None
    new_decorator_list: list[str] | None = None
    new_method_name: str | None = None
    new_returns: str | None = None


class VariableNameChange(Changes):
    """
    Represents a request to change the name of a variable. Changes take place over the entire codebase.

    Attributes:
        original_name (str): The original name of the variable.
        new_name (str): The new name to assign to the variable.
    """

    original_name: str
    new_name: str


class AddImport(Changes):
    """
    Represents an import statement to be added to a Python file.

    Args:
        module (str): The name of the module to be imported.
        names (list, optional): A list of names to be imported from the module. Defaults to None.
        asnames (list, optional): A list of aliases for the imported names. Defaults to None.
        objects (list, optional): A list of objects to be imported from the module. Defaults to None.
    """

    file_name: str
    module: str
    names: list | None = None
    asnames: list | None = None
    objects: list | None = None


class DeleteImport(Changes):
    """
    Represents a request to delete one or more imports from a Python module.

    Args:
        module (str): The name of the module to delete imports from.
        names (list, optional): A list of import names to delete. Defaults to None.
        asnames (list, optional): A list of import aliases to delete. Defaults to None.
        objects (list, optional): A list of import objects to delete. Defaults to None.
    """

    file_name: str
    module: str
    names: list | None = None
    asnames: list | None = None
    objects: list | None = None


class ModifyImport(Changes):
    """
    Represents a modification to an import statement in a Python file.

    Attributes:
        file_name (str): The name of the file containing the import statement.
        module (str): The name of the module being imported.
        new_names (list, optional): A list of new names to be imported from the module.
        new_asnames (list, optional): A list of new names to be imported from the module with an alias.
        new_objects (list, optional): A list of new objects to be imported from the module.
    """

    file_name: str
    module: str
    new_names: list | None = None
    new_asnames: list | None = None
    new_objects: list | None = None


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
