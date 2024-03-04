import json
import uuid
from instructor import OpenAISchema
from pydantic import Field
from agent.agent_functions.function_ops import (
    AddFunction,
    DeleteFunction,
    ModifyFunction,
)
from agent.agent_functions.class_ops import AddClass, DeleteClass, ModifyClass
from agent.agent_functions.method_ops import AddMethod, DeleteMethod, ModifyMethod
from agent.agent_functions.import_ops import AddImport, DeleteImport, ModifyImport

# Export all the entities
__all__ = [
    "AddFunction",
    "DeleteFunction",
    "ModifyFunction",
    "AddClass",
    "DeleteClass",
    "ModifyClass",
    "AddMethod",
    "DeleteMethod",
    "ModifyMethod",
    "AddImport",
    "DeleteImport",
    "ModifyImport",
    "VariableNameChange",
]


class VariableNameChange(OpenAISchema):
    """
    Represents a request to change the name of a variable throughout the entire codebase. This operation replaces all instances of the original variable name with a new name.
    """

    original_name: str
    new_name: str
    id: str

    def to_json(self) -> str:
        out = dict(id=self.id, original_name=self.original_name, new_name=self.new_name)
        return "\n\n```json\n" + json.dumps(out, indent=4) + "\n```\n"


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
