from http import HTTPStatus
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import sys
from uuid import uuid4
from agent.agent import CodingAgent
from agent.memory_manager import MemoryManager
from database.my_codebase import MyCodebase
from agent.openai_function_call import openai_function


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

codebase = MyCodebase("../")
tree = codebase.tree()

SYSTEM_PROMPT = f"""
You are an AI Coding assistant and a world class python programmer helping me work on a project.
The structure of the codebase is as follows:
{tree}
"""


@openai_function
def code_search(query: str) -> str:
    """
    Search the Human's codebase to see the most up to date code. This is useful when
    you are responsding to a question from the Human but were not given complete information.
    """
    return codebase.search(query)


agent = CodingAgent(
    MemoryManager(model="gpt-3.5-turbo-0613", system=SYSTEM_PROMPT),
    functions=[code_search.openai_schema],
    callables=[code_search.func],
)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            prompt = data.get("input")
            id = str(uuid4())
            for content in agent.query(prompt):
                if content is not None:
                    print(content)
                    await websocket.send_json({"id": id, "content": content})
                    sys.stdout.flush()
    except WebSocketDisconnect:
        # handle disconnection, e.g., cleanup operations, logging
        print("WebSocket disconnected")


@app.get("/system_prompt")
async def get_system_prompt():
    return {"system_prompt": agent.memory_manager.system}


@app.post("/update_system")
async def update_system_prompt(input: dict):
    agent.memory_manager.set_system(input.get("system_prompt"))
    print(agent.memory_manager.system)
    return HTTPStatus(200)
