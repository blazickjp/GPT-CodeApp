from sqlite3 import SQLITE_IOERR_COMMIT_ATOMIC
from openai import OpenAIAPI, OpenAIError
from instructor import patch
from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

CLIENT = patch(OpenAIAPI())
CHAT_HISTORY = dict()


class AgentType(str, Enum):
    TEACHER = "teacher"
    STUDENT_A = "student_a"
    STUDENT_B = "student_b"


for agent in AgentType:
    CHAT_HISTORY[agent.value] = []


def main():
    student_a, student_b, teacher = load_agents()
    speaker = None
    
    while True:
        speaker = select_speaker(last_speaker=speaker)
        


if __name__ == "__main__":
    main()
