import asyncio
import json
import random
import socket
from websockets import connect

async def wait_for_port(port: int, timeout: int = 60000) -> bool:
    start_time = asyncio.get_event_loop().time()
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(("127.0.0.1", port))
            sock.close()
            return True
        except Exception:
            if asyncio.get_event_loop().time() - start_time > timeout / 1000:
                raise ValueError(f"Port {port} not available after {timeout}ms")
            await asyncio.sleep(1)

async def send_message(sender_name: str, message_content: str, ws):
    corr_id = f"id{random.randint(0, 999999)}"
    escaped_name = f"'{sender_name}'" if " " in sender_name else sender_name
    cmd = f"@{escaped_name} {message_content}"
    message = json.dumps({"corrId": corr_id, "cmd": cmd})
    print(f"Sending: {message}")
    await ws.send(message)

async def send_image(sender_name: str, file_path: str, ws):
    corr_id = f"id{random.randint(0, 999999)}"
    escaped_name = f"'{sender_name}'" if " " in sender_name else sender_name
    cmd = f"/img @{escaped_name} {file_path}"
    message = json.dumps({"corrId": corr_id, "cmd": cmd})
    print(f"Sending: {message}")
    await ws.send(message)

async def subscribe_to_events(ws):
    corr_id = f"id{random.randint(0, 999999)}"
    await ws.send(json.dumps({"corrId": corr_id, "cmd": "/subscribe on"}))

async def get_invitation_link(ws):
    corr_id = f"id{random.randint(0, 999999)}"
    await ws.send(json.dumps({"corrId": corr_id, "cmd": "/connect"}))
    print("Requested invitation link...")

async def connect_websocket(port: int, message_handler):
    await wait_for_port(port)
    async with connect(f"ws://localhost:{port}") as ws:
        print("WebSocket connected")
        await subscribe_to_events(ws)
        await get_invitation_link(ws)

        async for message in ws:
            response = json.loads(message)
            print(f"Received: {response}")
            await message_handler(response, ws)