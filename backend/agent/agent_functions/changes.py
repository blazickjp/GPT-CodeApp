import ast
import astor
import difflib
from typing import List
from instructor import OpenAISchema


class Changes(OpenAISchema):
    """
    A class representing a list of operations that can be performed on a file.

    Attributes:
        ops (list): A list of operations that can be performed on a file.

    Usage:
        operations = Operations()
        operations.ops = [FunctionOperations(), ClassOperations(), MethodOperations(), ImportOperations()]
    """

    files: set = set()
    diffs: List[str] = []

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

    @classmethod
    def from_streaming_response(cls, completion):
        print("Here")
        print("Streaming: ", completion)
        json_chunks = cls.extract_json(completion)
        yield from cls.tasks_from_chunks(json_chunks)

    @classmethod
    def tasks_from_chunks(cls, json_chunks):
        started = False
        potential_object = ""
        print("Starting to stream")
        for chunk in json_chunks:
            potential_object += chunk
            if not started:
                if "[" in chunk:
                    started = True
                    potential_object = chunk[chunk.find("[") + 1 :]
                continue

            task_json, potential_object = cls.get_object(potential_object, 0)
            if task_json:
                obj = cls.task_type.model_validate_json(task_json)  # type: ignore
                yield obj

    @staticmethod
    def extract_json(completion):
        for chunk in completion:
            if chunk.choices:
                delta = chunk.choices[0].delta
                if delta.function_call:
                    if delta.function_call.arguments:
                        yield delta.function_call.arguments

    @staticmethod
    def get_object(str, stack):
        for i, c in enumerate(str):
            if c == "{":
                stack += 1
            if c == "}":
                stack -= 1
                if stack == 0:
                    return str[: i + 1], str[i + 2 :]
        return None, str


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
            elif isinstance(change, AddClass):
                new_class_node = self.create_class_node(change)
                node.body.append(new_class_node)
            elif isinstance(change, DeleteFunction):
                node.body = [
                    n
                    for n in node.body
                    if not (
                        isinstance(n, ast.FunctionDef)
                        and n.name == change.function_name
                    )
                ]
            elif isinstance(change, DeleteClass):
                node.body = [
                    n
                    for n in node.body
                    if not (isinstance(n, ast.ClassDef) and n.name == change.class_name)
                ]
        import_changes = [
            change for change in self.changes if isinstance(change, ImportOperations)
        ]
        for change in import_changes:
            for add_import in change.add_imports:
                new_import_node = self.create_import_node(add_import)
                node.body.insert(0, new_import_node)
            for delete_import in change.delete_imports:
                node.body = self.remove_import_node(node.body, delete_import)

        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node):
        # Handle renaming, adding, deleting, and modifying methods in a class
        for change in self.changes:
            if isinstance(change, ModifyClass) and node.name == change.name:
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
