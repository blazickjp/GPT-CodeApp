from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import openai
import sys
from uuid import uuid4

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        print(data)
        prompt = data.get("input")
        id = str(uuid4())
        print(id)

        for chunk in openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            stream=True,
        ):
            content = chunk["choices"][0].get("delta", {}).get("content")
            if content is not None:
                await websocket.send_json({"id": id, "content": content})
                sys.stdout.flush()
