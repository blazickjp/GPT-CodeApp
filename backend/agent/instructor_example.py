import json
from agent.agent_prompts import CHANGES_SYSTEM_PROMPT
from openai import OpenAI
from agent.agent_functions.file_ops import _OP_LIST, from_streaming_response
import time
import instructor


client = instructor.patch(OpenAI())

# Example return objects from the API

# {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"gpt-3.5-turbo-0613", "system_fingerprint": "fp_44709d6fcb", "choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":null}]}

# {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"gpt-3.5-turbo-0613", "system_fingerprint": "fp_44709d6fcb", "choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

# {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"gpt-3.5-turbo-0613", "system_fingerprint": "fp_44709d6fcb", "choices":[{"index":0,"delta":{"content":"!"},"finish_reason":null}]}

# ....

# {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"gpt-3.5-turbo-0613", "system_fingerprint": "fp_44709d6fcb", "choices":[{"index":0,"delta":{"content":" today"},"finish_reason":null}]}

# {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"gpt-3.5-turbo-0613", "system_fingerprint": "fp_44709d6fcb", "choices":[{"index":0,"delta":{"content":"?"},"finish_reason":null}]}

# {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1694268190,"model":"gpt-3.5-turbo-0613", "system_fingerprint": "fp_44709d6fcb", "choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

chunks = client.chat.completions.create(
    model="gpt-4-1106-preview",
    temperature=0.1,
    seed=1337,
    stream=True,
    tools=[
        {"type": "function", "function": cls.openai_schema} for cls in _OP_LIST.values()
    ],
    tool_choice="auto",
    messages=[
        {
            "role": "system",
            "content": CHANGES_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": "Add a hello world function to the file_ops.py file and a test for it in test_file_ops.py.",
        },
    ],
    max_tokens=1000,
)
for i in from_streaming_response(chunks, _OP_LIST):
    print(i)
    time.sleep(1)
# cls = _OP_LIST[tool_call.function.name](**json.loads(tool_call.function.arguments))
# print(cls)
"""
5.0 s: User(name='Ye Wenjie' job='Astrophysicist' age=50)
6.6 s: User(name='Wang Miao' job='Nanomaterials Researcher' age=40)
8.0 s: User(name='Shi Qiang' job='Detective' age=55)
9.4 s: User(name='Ding Yi' job='Theoretical Physicist' age=45)
10.6 s: User(name='Chang Weisi' job='Major General' age=60)
"""
# Notice that the first one would return at 5s bu the last one returned in 10s!
