import ast

from pydantic import BaseModel
import astor
from openai_function_call import OpenAISchema


class RenameImport(BaseModel):
    old_name: str
    new_name: str


class AddFunction(BaseModel):
    function_name: str
    args: str
    body: str
    decorator_list: list[str] = []
    returns: str | None = None


class DeleteFunction(BaseModel):
    function_name: str


class AddClass(BaseModel):
    class_name: str
    bases: list[str] = []
    body: str
    decorator_list: list[str] = []


class DeleteClass(BaseModel):
    class_name: str


class AddMethod(BaseModel):
    class_name: str
    method_name: str
    args: str
    body: str
    decorator_list: list[str] = []
    returns: str | None = None


class DeleteMethod(BaseModel):
    class_name: str
    method_name: str


class ModifyMethod(BaseModel):
    class_name: str
    method_name: str
    new_args: str | None = None
    new_body: str | None = None
    new_decorator_list: list[str] | None = None
    new_method_name: str | None = None
    new_returns: str | None = None


class ModifyFunction(BaseModel):
    function_name: str
    new_args: str | None = None
    new_body: str | None = None
    new_decorator_list: list[str] | None = None
    new_returns: str | None = None
    new_name: str | None = None


class ModifyClass(BaseModel):
    name: str
    new_bases: list[str] | None = None  # New base classes
    new_body: list | None = (
        None  # New body of the class, which might include method definitions etc.
    )
    new_decorator_list: list[str] | None = None  # New decorators for the class
    new_name: str | None = None  # New name for the class


class VariableNameChange(OpenAISchema):
    original_name: str
    new_name: str


class AddImport(BaseModel):
    module: str
    names: list | None = None
    asnames: list | None = None
    objects: list | None = None


class DeleteImport(BaseModel):
    module: str
    names: list | None = None
    asnames: list | None = None
    objects: list | None = None


class ModifyImport(BaseModel):
    module: str
    new_names: list | None = None
    new_asnames: list | None = None
    new_objects: list | None = None


class ImportOperations(OpenAISchema):
    add_imports: list[AddImport] = []
    delete_imports: list[DeleteImport] = []
    modify_imports: list[ModifyImport] = []


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

    def sort_changes(self, changes):
        # Implement sorting logic based on the type of changes and their dependencies.
        return sorted(changes, key=lambda change: change.priority)

    def is_conflict(self, change):
        # Implement conflict detection logic based on the current state of the code.
        return False


class CustomASTTransformer(ast.NodeTransformer):
    def __init__(self, changes):
        self.changes = changes
        super().__init__()

    def visit_ClassDef(self, node):
        # Check if this class needs to be modified
        for change in self.changes:
            if isinstance(change, ModifyClass) and node.name == change.name:
                # Modify base classes if new_bases is provided
                if change.new_bases is not None:
                    node.bases = [
                        ast.parse(base).body[0].value for base in change.new_bases
                    ]

                # Replace the entire body if new_body is provided
                if change.new_body is not None:
                    node.body = []
                    for item in change.new_body:
                        # Here it is assumed that new_body is a list of strings of valid Python code
                        node.body.extend(ast.parse(item).body)

                # Update decorators if new_decorator_list is provided
                if change.new_decorator_list is not None:
                    node.decorator_list = [
                        ast.parse(deco).body[0].value
                        for deco in change.new_decorator_list
                    ]
                # Update the name of the class if new_name is provided
                if change.new_name is not None:
                    node.name = change.new_name

                    # Fix locations in the AST
                ast.fix_missing_locations(node)

            elif isinstance(change, DeleteMethod) and change.class_name == node.name:
                # Filter out the method to delete from the body of the class
                node.body = [
                    item
                    for item in node.body
                    if not (
                        isinstance(item, ast.FunctionDef)
                        and item.name == change.method_name
                    )
                ]
                # Fix locations in the AST
                ast.fix_missing_locations(node)

            elif isinstance(change, AddMethod) and change.class_name == node.name:
                # Create a new method node
                args = ast.parse(f"def method({change.args}): pass").body[0].args
                new_method_node = ast.FunctionDef(
                    name=change.method_name,
                    args=args,
                    body=[ast.parse(change.body).body[0]],
                    decorator_list=[
                        ast.parse(d).body[0].value for d in change.decorator_list
                    ],
                    returns=ast.parse(change.returns).body[0].value
                    if change.returns
                    else None,
                )

                # Add the new method to the body of the class
                node.body.append(new_method_node)
                # Fix locations in the AST
                ast.fix_missing_locations(node)

            elif isinstance(change, ModifyMethod) and any(
                method.name == change.method_name
                for method in node.body
                if isinstance(method, ast.FunctionDef)
            ):
                for i, method in enumerate(node.body):
                    if (
                        isinstance(method, ast.FunctionDef)
                        and method.name == change.method_name
                    ):
                        if change.new_method_name:
                            method.name = change.new_method_name
                        if change.new_args:
                            # Parse the new arguments
                            args = (
                                ast.parse("def a(" + change.new_args + "): pass")
                                .body[0]
                                .args
                            )
                            # Add the arguments to the method
                            method.args = args
                        if change.new_body:
                            # Parse the new body
                            body = ast.parse(change.new_body).body
                            # Add the body to the method
                            method.body = body
                        if change.new_returns:
                            # Parse the new return statement
                            return_stmt = (
                                ast.parse("return " + change.new_returns).body[0].value
                            )
                            # Add the return statement to the end of the method body
                            method.body = return_stmt.value

                # Fix locations in the AST
                ast.fix_missing_locations(node)
                break

        return self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # Handle function-level changes such as ModifyFunction, AddFunction, and DeleteFunction
        for change in self.changes:
            if isinstance(change, ModifyFunction) and node.name == change.function_name:
                if change.new_args is not None:
                    node.args = (
                        ast.parse("def a(" + change.new_args + "): pass").body[0].args
                    )
                node.body = ast.parse(change.new_body).body
                if change.new_decorator_list is not None:
                    node.decorator_list = [
                        ast.parse(deco).body[0].value
                        for deco in change.new_decorator_list
                    ]
                if change.new_returns is not None:
                    node.returns = ast.parse(change.new_returns).body[0].value

        ast.fix_missing_locations(node)
        return self.generic_visit(node)

    def visit_Name(self, node):
        # Handle variable name changes
        for change in self.changes:
            if (
                isinstance(change, VariableNameChange)
                and node.id == change.original_name
            ):
                node.id = change.new_name

        ast.fix_missing_locations(node)
        return self.generic_visit(node)

    def visit_Module(self, node):
        # Handle module-level changes such as AddClass, DeleteClass, AddImport, and DeleteImport
        for change in self.changes:
            if isinstance(change, AddClass):
                new_class_node = ast.ClassDef(
                    name=change.class_name,
                    bases=[ast.Name(base, ast.Load()) for base in change.bases],
                    keywords=[],
                    body=ast.parse(change.body).body,
                    decorator_list=[],
                )
                node.body.append(new_class_node)

            if isinstance(change, DeleteClass):
                node.body = [
                    n
                    for n in node.body
                    if not (isinstance(n, ast.ClassDef) and n.name == change.class_name)
                ]

            if isinstance(change, ImportOperations):
                for add_import in change.add_imports:
                    if add_import.objects:
                        # 'from ... import ...' statement
                        new_import_node = ast.ImportFrom(
                            module=add_import.module,
                            names=[
                                ast.alias(name=obj, asname=None)
                                for obj in add_import.objects
                            ],
                            level=0,
                        )
                    else:
                        # 'import ...' statement
                        names = add_import.names if add_import.names is not None else []
                        asnames = (
                            add_import.asnames if add_import.asnames is not None else []
                        )
                        new_import_node = ast.Import(
                            names=[
                                ast.alias(name=name, asname=asname)
                                for name, asname in zip(names, asnames)
                                if name is not None
                            ]
                        )
                    node.body.insert(0, new_import_node)

                for delete_import in change.delete_imports:
                    new_imports = []
                    for item in node.body:
                        if (
                            isinstance(item, ast.ImportFrom)
                            and item.module == delete_import.module
                        ):
                            # Filter out the object to be deleted
                            item.names = [
                                alias
                                for alias in item.names
                                if alias.name not in delete_import.objects
                            ]
                            # Only add the import statement if there are remaining objects
                            if item.names:
                                new_imports.append(item)
                        else:
                            new_imports.append(item)
                    node.body = new_imports

                for modify_import in change.modify_imports:
                    if modify_import.objects:
                        # 'from ... import ...' statement
                        for n in node.body:
                            if (
                                isinstance(n, ast.ImportFrom)
                                and n.module == modify_import.module
                            ):
                                for alias in n.names:
                                    if alias.name in modify_import.objects:
                                        alias.name = modify_import.new_objects[
                                            modify_import.objects.index(alias.name)
                                        ]
                    else:
                        # 'import ...' statement
                        for n in node.body:
                            if isinstance(n, ast.Import):
                                for alias in n.names:
                                    if alias.name in modify_import.names:
                                        alias.name = modify_import.new_names[
                                            modify_import.names.index(alias.name)
                                        ]

            if isinstance(change, AddFunction):
                new_function_node = ast.FunctionDef(
                    name=change.function_name,
                    args=ast.arguments(
                        args=[],
                        vararg=None,
                        kwonlyargs=[],
                        kw_defaults=[],
                        kwarg=None,
                        defaults=[],
                        posonlyargs=[]
                        # Do not include posonlyargs
                    ),
                    body=[ast.parse(change.body).body[0]],
                    decorator_list=[
                        ast.parse(d).body[0].value for d in change.decorator_list
                    ],
                    returns=ast.parse(change.returns).body[0].value
                    if change.returns
                    else None,
                )
                node.body.append(new_function_node)

            elif isinstance(change, DeleteClass):
                # Logic for deleting a class
                node.body = [
                    n
                    for n in node.body
                    if not (isinstance(n, ast.ClassDef) and n.name == change.class_name)
                ]

            elif isinstance(change, ModifyFunction):
                # Find and modify the function definition
                for n in node.body:
                    if (
                        isinstance(n, ast.FunctionDef)
                        and n.name == change.function_name
                    ):
                        if change.new_name:
                            n.name = change.new_name
                        if change.new_body:
                            n.body = ast.parse(change.new_body).body

            elif isinstance(change, DeleteFunction):
                # Logic for deleting a function
                node.body = [
                    n
                    for n in node.body
                    if not (
                        isinstance(n, ast.FunctionDef)
                        and n.name == change.function_name
                    )
                ]

        ast.fix_missing_locations(node)
        # Continue processing the rest of the AST
        return self.generic_visit(node)

    def visit_Import(self, node):
        for change in self.changes:
            if isinstance(change, RenameImport):
                for alias in node.names:
                    if alias.name == change.old_name or alias.asname == change.old_name:
                        if alias.asname:
                            alias.asname = change.new_name
                        else:
                            alias.name = change.new_name
        return self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for change in self.changes:
            if isinstance(change, RenameImport):
                if node.module == change.old_name:
                    node.module = change.new_name
                for alias in node.names:
                    if alias.name == change.old_name:
                        alias.name = change.new_name
        return self.generic_visit(node)
