# import os
from ast import Call
from matplotlib.font_manager import json_load
import openai
import json
from typing import Any, List, Optional, Callable
from pydantic import BaseModel

# from agent.agent_functions import Program, File

GPT_MODEL = "gpt-3.5-turbo-0613"  # or any other chat model you want to use
MAX_TOKENS = 1000  # or any other number of tokens you want to use
TEMPERATURE = 0.2  # or any other temperature you want to use


class FunctionCall(BaseModel):
    name: Optional[str] = None
    arguments: str = ""


class Message(BaseModel):
    role: str
    content: str

    def to_dict(self):
        return {
            "role": self.role,
            "content": self.content,
        }


class CodingAgent:
    def __init__(
        self,
        memory_manager,
        functions: Optional[List[dict]] = None,
        callables: Optional[List[Callable]] = None,
    ):
        self.memory_manager = memory_manager
        self.functions = functions
        self.callables = callables
        self.GPT_MODEL = GPT_MODEL
        if callables:
            self.function_map = {
                func.__name__: func for func in callables if func is not None
            }
        print(f"Function Map: {self.function_map}")

    def query(self, input: str, command: Optional[str] = None) -> List[str]:
        print(f"Input Text: {input}")
        self.memory_manager.add_message("user", input)
        message_history = [
            Message(**i).to_dict() for i in self.memory_manager.get_messages()
        ]

        keyword_args = {
            "model": self.GPT_MODEL,
            "messages": message_history,
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE,
            "stream": True,
        }
        if self.functions:
            keyword_args["functions"] = self.functions
            keyword_args["function_call"] = "auto"
            function_to_call = FunctionCall()

        # Override normal function calling when function_name is provided
        if command:
            if command not in self.function_map:
                raise ValueError(f"Function {command} not registered with Agent")

            keyword_args["functions"] = [self.function_map.get(command).openai_schema]
            keyword_args["function_call"] = {"name": command}
            function_to_call = FunctionCall()

        for chunk in openai.ChatCompletion.create(**keyword_args):
            delta = chunk["choices"][0].get("delta", {})
            if "function_call" in delta:
                if "name" in delta.function_call:
                    function_to_call.name = delta.function_call["name"]
                if "arguments" in delta.function_call:
                    function_to_call.arguments += delta.function_call["arguments"]
            if chunk.choices[0].finish_reason == "stop":
                print(
                    f"\n\nFunc Call: {function_to_call.name}\n\n{function_to_call.arguments}"
                )
                args = json.loads(function_to_call.arguments)
                function_response = self.function_map[function_to_call.name](**args)
                function_response.save()
                print(f"Func Response: {json.dumps(function_response.to_dict())}")
                # function_message = {
                #     "role": "function",
                #     "name": function_to_call.name,
                #     "content": json.dumps(function_response.to_dict()),
                # }
                # message_history.append(function_message)
                # for chunk in openai.ChatCompletion.create(
                #     model=self.GPT_MODEL,
                #     messages=message_history,
                #     max_tokens=MAX_TOKENS,
                #     temperature=TEMPERATURE,
                #     stream=True,
                # ):
                #     content = chunk["choices"][0].get("delta", {}).get("content")
                yield json.dumps(function_response.to_dict())
            else:
                yield delta.get("content")
