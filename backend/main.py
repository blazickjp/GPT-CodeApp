# Base
import json
import os
from uuid import uuid4
import tiktoken

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from agent.agent import CodingAgent
from agent.memory_manager import MemoryManager
from database.my_codebase import MyCodebase, get_git_root
from openai_function_call import openai_function
from typing import Optional, List

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
cur = codebase.conn.cursor()

ENCODER = tiktoken.encoding_for_model("gpt-3.5-turbo")

agent = CodingAgent(
    MemoryManager(
        model="gpt-3.5-turbo-0613",
        tree=tree,
    ),
    # functions=[Shell.openai_schema],
    # callables=[Shell],
    # functions=[develop.openai_schema],
    # callables=[code_search.func],
)


@app.post("/message_streaming")
async def message_streaming(request: Request) -> StreamingResponse:
    # Get the input data from the POST request
    # function_data needs keys: "name", "input"
    data = await request.json()
    prompt = data.get("input")

    def stream():
        id = str(uuid4())
        accumulated_messages = {id: ""}
        for content in agent.query(prompt):
            if content is not None:
                accumulated_messages[id] += content
                # TODO: This is a hack to prevent multiple messages from being
                # processes at once. We should fix this on the client side.
                yield json.dumps({"id": id, "content": content}) + "\n"

        agent.memory_manager.add_message("assistant", accumulated_messages[id])

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.post("/edit_files")
async def edit_files(request: Request):
    try:
        data = await request.json()
        code = data.get("code")

        top_file = codebase.search(code, k=1)

        # Check if top_file exists
        if not top_file:
            return JSONResponse(
                status_code=404,
                content={"error": "No file found corresponding to the provided code."},
            )
        prompt = f"""
        You've been helping with a coding project and have been asked to update the following file
        with updated code shown below. Make sure that this code is correct and that it runs. Your
        system prompt and conversation history is being included to give you context on the task.
        Make sure you include the contents for the ENTIRE FILE, not just the code you've been asked to update.

        FULL FILE AND CONTENTS:
        {top_file}

        NEW CODE:
        {code}
        """
        print(f"Top File: {top_file[0:100]}")
        print("Running agent.edit_files")
        contents, program = agent.edit_files(prompt)

        # return json.dumps({"contents": contents}) + "\n"
        return JSONResponse(
            status_code=200, content={"old_file": top_file, "new_file": contents}
        )

    except Exception as e:
        # Catch any general exception
        return JSONResponse(
            status_code=500,
            content={
                "error": f"An error occurred while processing the request: {str(e)}"
            },
        )


@app.get("/system_prompt")
async def get_system_prompt():
    return {"system_prompt": agent.memory_manager.system}


@app.post("/update_system")
async def update_system_prompt(input: dict):
    agent.memory_manager.set_system(input.get("system_prompt"))
    return JSONResponse(status_code=200, content={})


@app.get("/get_functions")
async def get_functions():
    if agent.functions is None:
        return {
            "functions": [
                {"name": "The Agent has 0 Functions Loaded", "description": ""}
            ]
        }
    return {"functions": agent.functions}


@app.get("/get_messages")
async def get_messages(chatbox: bool | None = None):
    if len(agent.memory_manager.messages) == 1:
        return {"messages": []}
    else:
        return {"messages": agent.memory_manager.get_messages(chat_box=chatbox)[1:]}


@app.get("/get_summaries")
async def get_summaries(reset: bool | None = None):
    if reset:
        print("Refreshing Data")
        codebase._update_files_and_embeddings()

    cur.execute("SELECT DISTINCT file_path, summary, token_count FROM files")
    results = cur.fetchall()
    root_path = get_git_root(".")
    result = [
        {
            "file_path": os.path.relpath(file_path, root_path),
            "file_token_count": token_count,
            "summary": summary,
            "summary_token_count": len(ENCODER.encode(summary)),
        }
        for file_path, summary, token_count in results
    ]
    result = sorted(result, key=lambda x: x["file_path"])
    return result


@app.get("/generate_readme")
async def generate_readme():
    return {"readme": "Deprecated"}


@app.post("/set_summary_files_in_prompt")
async def set_summary_files_in_prompt(input: dict):
    if "files" not in input:
        return JSONResponse(status_code=400, content={"error": "missing files"})

    files = [os.path.join(get_git_root(), file) for file in input.get("files")]
    summaries = codebase.get_summaries()
    summaries = [f"{k}:\n{v}" for k, v in summaries.items() if k in files]
    additional_system_prompt_summaries = "\n\n".join(summaries)
    agent.memory_manager.system_file_summaries = additional_system_prompt_summaries
    agent.memory_manager.set_system()
    return JSONResponse(status_code=200, content={})


@app.post("/set_files_in_prompt")
async def set_files_in_prompt(input: dict):
    files = [os.path.join(get_git_root(), file) for file in input.get("files")]
    if not files:
        return JSONResponse(status_code=400, content={"error": "No files provided."})
    content = codebase.get_file_contents()
    content = [f"{k}:\n{v}" for k, v in content.items() if k in files]
    if not content:
        return JSONResponse(status_code=400, content={"error": "No files found."})
    additional_system_prompt_files = "\n\n".join(content)
    agent.memory_manager.system_file_contents = additional_system_prompt_files
    agent.memory_manager.set_system()
    return JSONResponse(status_code=200, content={})


@app.post("/set_model")
async def set_model(input: dict):
    model = input.get("model")
    agent.GPT_MODEL = model
    return JSONResponse(status_code=200, content={})
