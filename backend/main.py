import json
import psycopg2
import os
import tiktoken

from http import HTTPStatus
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

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
        tree=tree,
    ),
    functions=[code_search.openai_schema],
    callables=[code_search.func],
)


@app.post("/message_streaming")
async def message_streaming(request: Request):
    # Get the input data from the POST request
    data = await request.json()
    prompt = data.get("input")

    def stream():
        id = str(uuid4())
        accumulated_messages = {id: ""}
        for content in agent.query(prompt):
            if content is not None:
                accumulated_messages[id] += content
                yield json.dumps({"id": id, "content": content})

        agent.memory_manager.add_message("assistant", accumulated_messages[id])

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/system_prompt")
async def get_system_prompt():
    return {"system_prompt": agent.memory_manager.system}


@app.post("/update_system")
async def update_system_prompt(input: dict):
    agent.memory_manager.set_system(input.get("system_prompt"))
    return JSONResponse(status_code=200, content={})


@app.get("/get_functions")
async def get_functions():
    return {"functions": agent.functions}


@app.get("/get_messages")
async def get_messages():
    # if len(agent.memory_manager.messages) == 1:
    #     return {"messages": []}
    # else:
    return {"messages": agent.memory_manager.get_messages()}


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
    return {"readme": "Deprecated"}


@app.post("/set_summary_files_in_prompt")
async def set_summary_files_in_prompt(input: dict):
    files = [os.path.join(get_git_root(), file) for file in input.get("files")]
    summaries = codebase.get_summaries()
    summaries = [f"{k}:\n{v}" for k, v in summaries.items() if k in files]
    additional_system_prompt_summaries = "\n\n".join(summaries)
    agent.memory_manager.system_file_summaries = additional_system_prompt_summaries
    agent.memory_manager.set_system()
    return {}, HTTPStatus(400)


@app.post("/set_files_in_prompt")
async def set_files_in_prompt(input: dict):
    files = [os.path.join(get_git_root(), file) for file in input.get("files")]
    content = codebase.get_file_contents()
    content = [f"{k}:\n{v}" for k, v in content.items() if k in files]
    additional_system_prompt_files = "\n\n".join(content)
    agent.memory_manager.system_file_contents = additional_system_prompt_files
    agent.memory_manager.set_system()
    return HTTPStatus(404)
