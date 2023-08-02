# app_setup.py
import psycopg2
import os
from agent.agent import CodingAgent
from agent.memory_manager import MemoryManager
from database.my_codebase import MyCodebase
from psycopg2.extensions import connection
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Any, Callable
from pydantic import BaseModel
from agent.agent_functions import command_planner, single_file_edit


load_dotenv()
CODEAPP_DB_NAME = os.getenv("CODEAPP_DB_NAME")
CODEAPP_DB_USER = os.getenv("CODEAPP_DB_USER")
CODEAPP_DB_PW = os.getenv("CODEAPP_DB_PW")
CODEAPP_DB_HOST = os.getenv("CODEAPP_DB_HOST")
DIRECTORY = os.getenv("PROJECT_DIRECTORY")

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


def create_database_connection() -> connection:
    try:
        auth = {
            "dbname": CODEAPP_DB_NAME,
            "user": CODEAPP_DB_USER,
            "password": CODEAPP_DB_PW,
            "host": CODEAPP_DB_HOST,
        }
        conn = psycopg2.connect(**auth)
        print("Successfully connected to database")
        return conn
    except Exception as e:
        if CODEAPP_DB_USER is None or CODEAPP_DB_USER == "USER_FROM_SETUP_STEP4":
            raise Exception(
                """
                Failed to connect to database.
                Credentials not set or changed in .env file or .env file is missing.
                Please set the following environment variables in the .env file in the root directory:
                CODEAPP_DB_NAME, CODEAPP_DB_USER, CODEAPP_DB_PW, CODEAPP_DB_HOST
                """
            )
        else:
            raise e


DB_CONNECTION = create_database_connection()


def setup_memory_manager(tree: Optional[str]) -> MemoryManager:
    memory_manager = MemoryManager(db_connection=DB_CONNECTION, tree=tree)
    return memory_manager


def setup_codebase() -> MyCodebase:
    my_codebase = MyCodebase(directory=DIRECTORY, db_connection=DB_CONNECTION)
    return my_codebase


def setup_app() -> CodingAgent:
    codebase = setup_codebase()
    memory = setup_memory_manager(tree=codebase.tree())
    agent = CodingAgent(
        memory_manager=memory, callables=[command_planner.func, single_file_edit.func]
    )
    return agent, codebase
