from pydantic import BaseModel


class AddFunction(BaseModel):
    """
    Represents a function to be added to a Python file.

    Args:
        function_name (str): The name of the function.
        args (str): The arguments of the function.
        body (str): The body of the function.
        decorator_list (list[str], optional): The list of decorators applied to the function. Defaults to [].
        returns (str | None, optional): The return type of the function. Defaults to None.
    """

    function_name: str
    args: str
    body: str
    decorator_list: list[str] = []
    returns: str | None = None


class DeleteFunction(BaseModel):
    """
    Represents a request to delete a function from the agent.

    Attributes:
        function_name (str): The name of the function to delete.
    """

    function_name: str


class ModifyFunction(BaseModel):
    """
    A class representing modifications to a function.

    Attributes:
        function_name (str): The name of the function to modify.
        new_args (str | None): The new arguments for the function, if any.
        new_body (str | None): The new body of the function, if any.
        new_decorator_list (list[str] | None): The new list of decorators for the function, if any.
        new_returns (str | None): The new return type for the function, if any.
        new_name (str | None): The new name for the function, if any.
    """

    function_name: str
    new_args: str | None = None
    new_body: str | None = None
    new_decorator_list: list[str] | None = None
    new_returns: str | None = None
    new_name: str | None = None


class AddClass(BaseModel):
    """Represents a class to be added to a file.

    Attributes:
        class_name (str): The name of the class.
        bases (list[str], optional): The base classes of the class. Defaults to an empty list.
        body (str): The body of the class.
        decorator_list (list[str], optional): The decorators applied to the class. Defaults to an empty list.
    """

    class_name: str
    bases: list[str] = []
    body: str
    decorator_list: list[str] = []


class DeleteClass(BaseModel):
    """Represents a class to be deleted.

    Attributes:
        class_name (str): The name of the class to be deleted.
    """

    class_name: str


class ModifyClass(BaseModel):
    """Represents a request to modify a Python class.

    Attributes:
        name (str): The name of the class to modify.
        new_bases (list[str], optional): The new base classes for the class.
        new_body (list, optional): The new body of the class, which might include
            method definitions, etc.
        new_decorator_list (list[str], optional): The new decorators for the class.
        new_name (str, optional): The new name for the class.
    """

    name: str
    new_bases: list[str] | None = None
    new_body: list | None = None
    new_decorator_list: list[str] | None = None
    new_name: str | None = None


class ModifyClass(BaseModel):
    name: str
    new_bases: list[str] | None = None  # New base classes
    new_body: list | None = (
        None  # New body of the class, which might include method definitions etc.
    )
    new_decorator_list: list[str] | None = None  # New decorators for the class
    new_name: str | None = None  # New name for the class


class AddMethod(BaseModel):
    """
    Represents a method to be added to a class.

    Attributes:
        class_name (str): The name of the class to which the method will be added.
        method_name (str): The name of the method.
        args (str): The arguments of the method.
        body (str): The body of the method.
        decorator_list (list[str], optional): The list of decorators to be applied to the method. Defaults to [].
        returns (str, optional): The return type of the method. Defaults to None.
    """

    class_name: str
    method_name: str
    args: str
    body: str
    decorator_list: list[str] = []
    returns: str | None = None


class DeleteMethod(BaseModel):
    """Represents a method to be deleted from a class.

    Attributes:
        class_name (str): The name of the class containing the method.
        method_name (str): The name of the method to be deleted.
    """

    class_name: str
    method_name: str


class ModifyMethod(BaseModel):
    """Represents a method modification operation.

    Attributes:
        class_name (str): The name of the class containing the method to be modified.
        method_name (str): The name of the method to be modified.
        new_args (str, optional): The new arguments for the method. Defaults to None.
        new_body (str, optional): The new body of the method. Defaults to None.
        new_decorator_list (list[str], optional): The new list of decorators for the method. Defaults to None.
        new_method_name (str, optional): The new name for the method. Defaults to None.
        new_returns (str, optional): The new return type for the method. Defaults to None.
    """

    class_name: str
    method_name: str
    new_args: str | None = None
    new_body: str | None = None
    new_decorator_list: list[str] | None = None
    new_method_name: str | None = None
    new_returns: str | None = None


class VariableNameChange(BaseModel):
    """
    Represents a request to change the name of a variable.

    Attributes:
        original_name (str): The original name of the variable.
        new_name (str): The new name to assign to the variable.
    """

    original_name: str
    new_name: str


class AddImport(BaseModel):
    """
    Represents an import statement to be added to a Python file.

    Args:
        module (str): The name of the module to be imported.
        names (list, optional): A list of names to be imported from the module. Defaults to None.
        asnames (list, optional): A list of aliases for the imported names. Defaults to None.
        objects (list, optional): A list of objects to be imported from the module. Defaults to None.
    """

    module: str
    names: list | None = None
    asnames: list | None = None
    objects: list | None = None


class DeleteImport(BaseModel):
    """
    Represents a request to delete one or more imports from a Python module.

    Args:
        module (str): The name of the module to delete imports from.
        names (list, optional): A list of import names to delete. Defaults to None.
        asnames (list, optional): A list of import aliases to delete. Defaults to None.
        objects (list, optional): A list of import objects to delete. Defaults to None.
    """

    module: str
    names: list | None = None
    asnames: list | None = None
    objects: list | None = None


class ModifyImport(BaseModel):
    """
    Represents a modification to an import statement in a Python file.

    Attributes:
        module (str): The name of the module being imported.
        new_names (list, optional): A list of new names to be imported from the module.
        new_asnames (list, optional): A list of new names to be imported from the module with an alias.
        new_objects (list, optional): A list of new objects to be imported from the module.
    """

    module: str
    new_names: list | None = None
    new_asnames: list | None = None
    new_objects: list | None = None


class ImportOperations(BaseModel):
    """
    Represents a set of operations to perform on an import statement in a Python file.

    Attributes:
        file_name (str): The name of the file to perform the import operations on.
        add_imports (List[AddImport]): A list of import statements to add to the file.
        delete_imports (List[DeleteImport]): A list of import statements to delete from the file.
        modify_imports (List[ModifyImport]): A list of import statements to modify in the file.
    """

    file_name: str
    add_imports: list[AddImport] = []
    delete_imports: list[DeleteImport] = []
    modify_imports: list[ModifyImport] = []


class FunctionOperations(BaseModel):
    """Represents a set of operations to be performed on a file's functions.

    Attributes:
        file_name (str): The name of the file to operate on.
        add_functions (list[AddFunction]): A list of functions to add to the file.
        delete_functions (list[DeleteFunction]): A list of functions to delete from the file.
        modify_functions (list[ModifyFunction]): A list of functions to modify in the file.
    """

    file_name: str
    add_functions: list[AddFunction] = []
    delete_functions: list[DeleteFunction] = []
    modify_functions: list[ModifyFunction] = []


class ClassOperations(BaseModel):
    """Represents a set of operations to perform on a file's classes.

    Attributes:
        file_name (str): The name of the file to perform the operations on.
        add_classes (list[AddClass]): A list of classes to add to the file.
        delete_classes (list[DeleteClass]): A list of classes to delete from the file.
        modify_classes (list[ModifyClass]): A list of classes to modify in the file.
    """

    file_name: str
    add_classes: list[AddClass] = []
    delete_classes: list[DeleteClass] = []
    modify_classes: list[ModifyClass] = []


class MethodOperations(BaseModel):
    """Represents a set of operations to be performed on a file's methods.

    Attributes:
        file_name (str): The name of the file to perform the operations on.
        add_methods (list[AddMethod]): A list of methods to be added to the file.
        delete_methods (list[DeleteMethod]): A list of methods to be deleted from the file.
        modify_methods (list[ModifyMethod]): A list of methods to be modified in the file.
    """

    file_name: str
    add_methods: list[AddMethod] = []
    delete_methods: list[DeleteMethod] = []
    modify_methods: list[ModifyMethod] = []
