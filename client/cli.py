import os
import asyncio
import socket
import subprocess
from dotenv import load_dotenv

load_dotenv()

SIMPLEX_PATH = os.getenv("SIMPLEX_PATH")
SIMPLEX_DB = os.getenv("SIMPLEX_DB")
PORT = int(os.getenv("PORT", "8000"))

if not SIMPLEX_PATH or not SIMPLEX_DB:
    raise ValueError("SIMPLEX_PATH and SIMPLEX_DB must be set in the .env file")

async def check_port_in_use(port: int) -> bool:
    loop = asyncio.get_event_loop()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        await loop.run_in_executor(None, sock.bind, ("127.0.0.1", port))
        sock.close()
        return False
    except OSError:
        return True
    finally:
        sock.close()

async def start_client(port: int = PORT) -> subprocess.Popen:
    print(f"Starting SimpleX CLI on port {port}...")
    command = f'"{SIMPLEX_PATH}" -d "{SIMPLEX_DB}" -p {port}'
    print(f"Command: {command}")
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        text=True
    )

    async def log_output(stream, prefix):
        while True:
            line = await asyncio.get_event_loop().run_in_executor(None, stream.readline)
            if not line:
                break
            print(f"{prefix}: {line.strip()}")

    asyncio.create_task(log_output(process.stdout, "CLI"))
    asyncio.create_task(log_output(process.stderr, "CLI Error"))

    await asyncio.sleep(1)
    return process