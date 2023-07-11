import sys
import psycopg2
import os
import subprocess
import tiktoken

from http import HTTPStatus
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from agent.agent import CodingAgent
from agent.memory_manager import MemoryManager
from database.my_codebase import MyCodebase, get_git_root
from agent.openai_function_call import openai_function

conn = psycopg2.connect(
    host="localhost", database="memory", user="joe", password="1234"
)
cur = conn.cursor()

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

SYSTEM_PROMPT = """
You are an AI Pair Prograamer and a world class python developer helping the Humar work on a project.

#### Project Details and Contextual Information ####
The directory structure of the codebase is as follows:
{}

File Contents the Human has included to assist you in your work:
{}

File Summaries the Human has included to assist you in your work:
{}

Happy Programming!
"""
ENCODER = tiktoken.encoding_for_model("gpt-3.5-turbo")


@openai_function
def code_search(query: str) -> str:
    """
    Search the Human's codebase to see the most up to date code. This is useful when
    you are responsding to a question from the Human but need additional information from their code.
    The function returns the top 2 results which will be the whole file's content.
    Your input query should be a string which semantically matches the code you are looking for.
    """
    return codebase.search(query)


agent = CodingAgent(
    MemoryManager(
        model="gpt-3.5-turbo-0613",
        system=SYSTEM_PROMPT.format(tree, "None", "None", "None"),
    ),
    functions=[code_search.openai_schema],
    callables=[code_search.func],
)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    accumulated_messages = {}
    try:
        while True:
            data = await websocket.receive_json()
            prompt = data.get("input")
            id = str(uuid4())
            for content in agent.query(prompt):
                if content is not None:
                    if id not in accumulated_messages:
                        accumulated_messages[id] = ""
                    accumulated_messages[id] += content
                    await websocket.send_json({"id": id, "content": content})
                    sys.stdout.flush()
            agent.memory_manager.add_message("assistant", accumulated_messages[id])

    except WebSocketDisconnect:
        accumulated_messages = {}
        print("WebSocket disconnected")


@app.get("/system_prompt")
async def get_system_prompt():
    return {"system_prompt": agent.memory_manager.system}


@app.post("/update_system")
async def update_system_prompt(input: dict):
    agent.memory_manager.set_system(input.get("system_prompt"))
    return HTTPStatus(200)


@app.get("/get_functions")
async def get_functions():
    return {"functions": agent.functions}


@app.get("/get_messages")
async def get_messages():
    if len(agent.memory_manager.messages) == 1:
        return {"messages": []}
    else:
        return {"messages": agent.memory_manager.messages[1:]}


@app.get("/get_summaries")
async def get_summaries():
    cur.execute("SELECT DISTINCT file_path, summary, token_count FROM files")
    results = cur.fetchall()
    root_path = get_git_root(".")

    result = [
        {
            "file_path": os.path.relpath(file_path, root_path),
            "summary": summary,
            "file_token_count": token_count,
            "summary_token_count": len(ENCODER.encode(summary)),
        }
        for file_path, summary, token_count in results
    ]
    result = sorted(result, key=lambda x: x["file_path"])
    return result


@app.get("/generate_readme")
async def generate_readme():
    # readme = codebase.generate_readme()
    return {"readme": "Deprecated"}


@app.post("/set_summary_files_in_prompt")
async def set_summary_files_in_prompt(input: dict):
    # files = input.get("files")
    # files = [codebase.get_file_path(file) for file in files]
    # agent.memory_manager.set_summary_files(files)
    return HTTPStatus(200)


@app.post("/set_files_in_prompt")
async def set_files_in_prompt(input: dict):
    # files = input.get("files")
    # files = [codebase.get_file_path(file) for file in files]
    # agent.memory_manager.set_files(files)
    return HTTPStatus(200)
