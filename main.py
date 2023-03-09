import json
import requests

from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE2NzgzNTk1NjIsImV4cCI6MTY3ODM2MzE2Miwicm9sZXMiOlsiUk9MRV9VU0VSIl0sInVzZXJuYW1lIjoidXNlckBleGFtcGxlLmNvbSJ9.V234UEMWG4A3QURw-aRsVj5w3zEIStk4QkiWRVkhKdJZjVSTL-y15x4u272HcJTYG4u0Ib97QIeF2ayp10ai6kSucCaQ87TVOTCxvisOMRU0vmhSpjga5H_-ApcIROtIZTz6bNK-mugMevpDPhL7cwFn2yZYapHq-EYKA-MaDVK5Z7DmBHJJJ0dlGKd3VA0UaYeTlluhAJw7kSsvsObRzArz3SeFOFChjFUIJfDbsaa4ae8yNnufWptf8AhEaeCdxNimYRcARRqtMFwpzpReeBtKVmYEfNs_gyeBIFIBOX8kDfoM01UEeea0gFCPt_UEz-kxB5-qC4TeIkM9T65kDQ'
            document.querySelector("#ws-id").textContent = token;
            var ws = new WebSocket(`ws://localhost:8000/ws/${token}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    await manager.connect(websocket)
    url = "http://127.0.0.1:8001/api/users/1/info"

    headers = {
        'Accept': 'application/ld+json',
        'Content-type': 'application/json',
        'Authorization': f"Bearer {token}"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        # ok
        print('Requête réussie', response.status_code)
        data = json.loads(response.text)
        nickname = data.get('nickname')
    else:
        print('Requête échouée', response.status_code)

    try:
        while True:
            data = await websocket.receive_text()
            # await manager.send_personal_message(f"You wrote: {nickname}", websocket)
            await manager.broadcast(f"Client {nickname} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client {nickname} left the chat")
