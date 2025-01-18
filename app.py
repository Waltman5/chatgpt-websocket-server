import asyncio
import json
import os
import websockets
from websockets import serve, exceptions

# -- Import NotDiamond
from notdiamond import NotDiamond

# -- Initialize NotDiamond client once (not inside the loop)
client = NotDiamond()

async def process_message(websocket, path):
    async for data in websocket:
        try:
            conversation = json.loads(data)
            user_message = conversation[-1]["content"].strip()

            # -- Call NotDiamond chat completion
            result, usage_info, provider = client.chat.completions.create(
                messages=[{"role": "user", "content": user_message}],
                model=[
                    "openai/gpt-4o-mini",
                    "perplexity/llama-3.1-sonar-large-128k-online"
                ],
                # The library chooses the best model according to 'tradeoff'
                tradeoff='cost'
            )

            # provider.model tells you which model was actually used.
            print("LLM called:", provider.model)

            # The final text output from the model
            reply = result.content
            if not reply:
                reply = "⚠️ Sorry, I couldn't generate a response."

            print("LLM output:", reply)

            # Send the reply back to the user
            await websocket.send(reply)

        except Exception as e:
            print(f"⚠️ Error: {e}")
            try:
                await websocket.send(f"⚠️ Error: {e}")
            except exceptions.ConnectionClosedOK:
                print("Client disconnected before receiving error message.")
            return

async def main():
    print("✅ WebSocket server is running on ws://0.0.0.0:9000 ...")
    async with serve(process_message, "0.0.0.0", 9000):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
