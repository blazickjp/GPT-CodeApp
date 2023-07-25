# import os
import openai
import json
from typing import List, Optional
from agent.agent_functions import Program, File

GPT_MODEL = "gpt-3.5-turbo-0613"  # or any other chat model you want to use
MAX_TOKENS = 1000  # or any other number of tokens you want to use
TEMPERATURE = 0.2  # or any other temperature you want to use


class CodingAgent:
    def __init__(self, memory_manager, functions=None, callables=[None]):
        """
        Initializes a CodingAgent object.

        Args:
            memory_manager (MemoryManager): An instance of MemoryManager class for managing conversation history.
            functions (list, optional): A list of function objects that can be called by the agent. Defaults to None.
        """
        self.memory_manager = memory_manager
        self.functions = functions
        self.GPT_MODEL = GPT_MODEL
        if callables:
            self.function_map = {
                func.__name__: func for func in callables if func is not None
            }  # Create a map of function names to functions

    def query(self, input_text: str) -> List[str]:
        """
        Conducts a conversation with the agent by providing an input text.

        Args:
            input_text (str): The user's input text.
        Returns:
            str: The output text generated by the agent.
        """
        print(f"Input Text: {input_text}")
        self.memory_manager.add_message("user", input_text)
        message_history = [
            {"role": i["role"], "content": i["content"]}
            for i in self.memory_manager.get_messages()
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
            func_call = {
                "name": None,
                "arguments": "",
            }

        for chunk in openai.ChatCompletion.create(**keyword_args):
            delta = chunk["choices"][0].get("delta", {})
            if "function_call" in delta:
                if "name" in delta.function_call:
                    func_call["name"] = delta.function_call["name"]
                if "arguments" in delta.function_call:
                    func_call["arguments"] += delta.function_call["arguments"]
            if chunk.choices[0].finish_reason == "function_call":
                print(f"Func Call: {func_call}")
                function_response = {
                    "role": "assistant",
                    "content": json.dumps(
                        obj=self.function_map[func_call["name"]](func_call["arguments"])
                    ),
                }
                message_history.append(function_response)
                for chunk in openai.ChatCompletion.create(
                    model=self.GPT_MODEL,
                    messages=message_history,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    stream=True,
                ):
                    content = chunk["choices"][0].get("delta", {}).get("content")
                    yield content
            else:
                yield delta.get("content")

    def edit_files(self, data: str, save: Optional[bool] = None) -> None:
        """
        Takes in natural language instructions which describe files and code to be written
        by another AI agent. Be as descriptive as possible in you input.
        """
        message_history = [
            {"role": i["role"], "content": i["content"]}
            for i in self.memory_manager.get_messages()
        ]
        message_history.append({"role": "user", "content": data})

        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            temperature=0.1,
            max_tokens=2000,
            functions=[Program.openai_schema],
            function_call={"name": Program.openai_schema["name"]},
            messages=message_history,
        )

        program = Program.from_response(completion)
        out = ""
        for file in program.files:
            out += f"File: {file.name}\nContents:\n{file.contents}\n"
            if save:
                file.save()
                print("Saved")
        return out, program
