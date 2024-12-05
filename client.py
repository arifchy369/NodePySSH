import asyncio
import websockets
import sys
import tty
import json
import os
import base64
tty.setraw(sys.stdin)

intro = "The custom SSH tools were created with a Node.js server and a Python client.\r\n©Arif Chowdhury\n\r"

#SERVER INFORMATION
USERNAME = "test@user"
PASSWORD = "test_pass"
HOST="wss://yourserver.com" #REPLACE WITH YOUR WEBSOCKET SERVER ENDPOINT

def get_terminal_size():
    cols,rows=os.get_terminal_size()
    return cols, rows


async def read_input():
    """Reads input asynchronously and handles raw input correctly."""
    loop = asyncio.get_event_loop()
    try:
        # Read from stdin in raw mode
        input_data = await loop.run_in_executor(None, lambda: os.read(sys.stdin.fileno(), 1000000000))
        return (input_data).decode()
    except Exception as e:
        print(f"Error reading input: {e}")
        return ""

async def send_input(ws):
    while True:
        try:
            command = await read_input()
            if command:  # Process only non-empty input
                # Handle special cases for Enter key or quit commands
                await ws.send(json.dumps({"type": "input", "data": command}))
        except Exception as e:
            print(f"Error in send_input: {e}")
            break


async def receive_output(ws):
    async for message in ws:
        response = json.loads(message)
        if response["type"] == "output":
            data = response["data"]
            if data.encode()==b'logout\r\n':
            	os._exit(0)
            print(data, end="", flush=True)
        elif response["type"] == "auth":
            if response["status"] == "failure":
                print("Authentication failed!\r")
                await ws.close()
                os._exit(0)
                break
            elif response["status"] == "success":
                print("Authentication successful!\r\n")
                print(intro)

async def send_resize(ws):
    last_size = None
    while True:
        await asyncio.sleep(0.5)
        cols, rows = get_terminal_size()
        if last_size != (cols, rows):
            last_size = (cols, rows)
            await ws.send(json.dumps({"type": "resize", "data": {"cols": cols, "rows": rows}}))

async def main():
    async with websockets.connect(HOST) as ws:
        await ws.send(json.dumps({"username": USERNAME, "password": PASSWORD}))

        await asyncio.gather(
            send_input(ws),
            receive_output(ws),
            send_resize(ws)
        )


try:
	asyncio.run(main())
except Exception as e:
	print(e)
