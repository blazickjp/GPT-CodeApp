import json
from instructor import OpenAISchema
from pydantic import Field
from agent.agent_functions.function_ops import AddFunction, DeleteFunction, ModifyFunction
from agent.agent_functions.class_ops import AddClass, DeleteClass, ModifyClass
from agent.agent_functions.method_ops import AddMethod, DeleteMethod, ModifyMethod
from agent.agent_functions.import_ops import AddImport, DeleteImport, ModifyImport

class VariableNameChange(OpenAISchema):
    """
    Represents a request to change the name of a variable. Changes take place over the entire codebase.
    """

    original_name: str = Field(..., description="The original name of the variable.")
    new_name: str = Field(..., description="The new name of the variable.")

    def to_string(self):
        out = dict(original_name=self.original_name, new_name=self.new_name)
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
