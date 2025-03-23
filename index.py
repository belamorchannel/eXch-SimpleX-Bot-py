import sys
import os
import asyncio
from dotenv import load_dotenv
from client.cli import start_client
from websocket.websock import connect_websocket
from main.bot import Bot

sys.path.append("C:\\Users\\asket\\OneDrive\\Рабочий стол\\Pypy")
print("Python path:", sys.path)

load_dotenv()

async def start_bot():
    print("Starting..")
    try:
        await start_client(int(os.getenv("PORT")))
        print("SimpleX CLI started")

        bot = Bot(None)
        await connect_websocket(int(os.getenv("PORT")), bot.handle_message)
    except Exception as e:
        print(f"Failed to start SimpleX CLI: {str(e)}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(start_bot())