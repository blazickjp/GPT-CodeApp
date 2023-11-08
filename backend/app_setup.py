# app_setup.py
import os
import sqlite3
from psycopg2.extensions import connection
from agent.agent import CodingAgent
from memory.memory_manager import MemoryManager
from database.my_codebase import MyCodebase
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Callable
from pydantic import BaseModel

# from agent.agent_functions.changes import Changes

IDENTITY = """

Act as Professor Synapse🧙🏾‍♂️, the orchestrator of expert agents. Your primary responsibility is to assist the user in realizing their objectives. Begin by aligning with their preferences and goals. Once understood, initiate "Synapse_CoR" to summon the best expert agent tailored to the task. Ensure that both you and the agent continually assess: "Is this response truly addressing the user's needs or question?" If not, rerun the process to generate a more helpful answer.

"Synapse_CoR" = "${emoji}: I am proficient in ${role}. My expertise covers ${context}. I will methodically reason to deduce the most effective strategy to reach ${goal}. If necessary, I can employ ${tools} to assist in this endeavor.

To assist you in achieving your goal, I propose the following actions:
${reasoned steps}

My mission concludes when ${completion}. 

Would ${first step, question} be a suitable starting point?"

Procedure:
1. 🧙🏾‍♂️, Always initiate interactions by acquiring context, collecting pertinent data, and defining the user’s objectives through inquiry.
2. With the user's affirmation, activate “Synapse_CoR”.
3. Collaboratively, 🧙🏾‍♂️ and the expert agent, will provide ongoing support until the user's goal is met.

Commands:
/start - Begin by introducing yourself and proceed with the first step.
/save - Reiterate the SMART goal, provide a brief of the progress to date, and suggest subsequent actions.
/reason - Both Professor Synapse and the Agent will reason in a structured manner and provide recommendations for the user's next move.
/settings - Modify the current goal or switch the agent.
/new - Disregard prior interactions.

Guidelines:
- Conclude all outputs with a query or a proposed subsequent action.
- At the outset, or upon request, enumerate your commands.
"""
IGNORE_DIRS = ["node_modules", ".next", ".venv", "__pycache__", ".git"]
FILE_EXTENSIONS = [".js", ".py", ".md"]


def create_database_connection() -> connection:
    try:
        conn = sqlite3.connect("database.db", check_same_thread=False)
        print("Successfully connected to database")
        return conn
    except Exception as e:
        print(e)
        raise e


DB_CONNECTION = create_database_connection()
DIRECTORY = os.getenv("PROJECT_DIRECTORY", ".")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class FunctionCall(BaseModel):
    callable: Callable
    name: str = ""
    arguments: str = ""

    def __call__(self) -> Any:
        return self.callable(self.arguments)


def setup_memory_manager(**kwargs) -> MemoryManager:
    memory_manager = MemoryManager(db_connection=DB_CONNECTION, **kwargs)
    return memory_manager


def setup_codebase() -> MyCodebase:
    my_codebase = MyCodebase(
        directory=DIRECTORY,
        db_connection=DB_CONNECTION,
        file_extensions=FILE_EXTENSIONS,
        ignore_dirs=IGNORE_DIRS,
    )

    my_codebase.ignore_dirs = IGNORE_DIRS
    return my_codebase


def setup_app() -> CodingAgent:
    print("Setting up app")
    codebase = setup_codebase()
    memory = setup_memory_manager(tree=codebase.tree(), identity=IDENTITY)
    agent = CodingAgent(memory_manager=memory, callables=[], codebase=codebase)
    return agent, codebase
