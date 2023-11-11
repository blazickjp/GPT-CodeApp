import time
import json
from openai import OpenAI

from agent_functions.file_ops import AddFunction

import instructor


client = instructor.patch(OpenAI())


def stream_extract(input: str, cls):
    # print(json.dumps(Changes.openai_schema, indent=2))
    completion = client.chat.completions.create(
        model="gpt-4-1106-preview",
        temperature=0.1,
        # stream=True,
        tools=[
            {
                "type": "function",
                "function": cls.openai_schema,
            }
        ],
        tool_choice="auto",
        messages=[
            {
                "role": "system",
                "content": "You are a perfect coding system using the Changes class to alter a codebase",
            },
            {
                "role": "user",
                "content": (
                    "Add a hello world function to the file_ops.py file and a test for it in test_file_ops.py"
                ),
            },
        ],
        max_tokens=1000,
    )
    return completion


start = time.time()
test = stream_extract(
    input="Create 5 characters from the book Three Body Problem",
    cls=AddFunction,
)
print(test)
"""
5.0 s: User(name='Ye Wenjie' job='Astrophysicist' age=50)
6.6 s: User(name='Wang Miao' job='Nanomaterials Researcher' age=40)
8.0 s: User(name='Shi Qiang' job='Detective' age=55)
9.4 s: User(name='Ding Yi' job='Theoretical Physicist' age=45)
10.6 s: User(name='Chang Weisi' job='Major General' age=60)
"""
# Notice that the first one would return at 5s bu the last one returned in 10s!
