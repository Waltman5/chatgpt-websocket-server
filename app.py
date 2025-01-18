import asyncio
import json
import os
import websockets
from websockets import serve, exceptions

# 1) Import the NotDiamond library
from notdiamond import NotDiamond

# 2) Read your NotDiamond API key from the 'onboarding' env variable on Render
NOTDIAMOND_API_KEY = os.getenv("onboarding")

if not NOTDIAMOND_API_KEY:
    print("⚠️  WARNING: The environment variable 'onboarding' is not set.")
    print("    Please set it in Render to your NotDiamond API key.")
    # Optionally, you can quit here if the key is mandatory:
    # import sys
    # sys.exit(1)
else:
    print("✅ Found NotDiamond API key in 'onboarding' environment variable.")

# 3) Initialize the NotDiamond client with your key
#    This ensures the correct key is used for authentication.
client = NotDiamond(api_key=NOTDIAMOND_API_KEY)

async def process_message(websocket, path):
    async for data in websocket:
        try:
            # 4) Parse the received message
            conversation = json.loads(data)
            user_message = conversation[-1]["content"].strip()

            # 5) Create a chat completion via NotDiamond
            result, usage_info, provider = client.chat.completions.create(
                messages=[{"role": "user", "content": user_message}],
                model=[
                    "openai/gpt-4o-mini",
                    "perplexity/llama-3.1-sonar-large-128k-online"
                ],
                tradeoff='cost'  # uses the best model based on cost vs. performance
            )

            # 6) Debug logs
            print("LLM called:", provider.model)  # Which model was used?
            reply = result.content
            if not reply:
                reply = "⚠️ Sorry, I couldn't generate a response."
            print("LLM output:", reply)

            # 7) Send the response back to the client
            await websocket.send(reply)

        except Exception as e:
            print(f"⚠️ Error in process_message: {e}")
            try:
                await websocket.send(f"⚠️ Error: {e}")
            except exceptions.ConnectionClosedOK:
                print("Client disconnected before receiving error message.")
            return

async def main():
    print("✅ WebSocket server is running on ws://0.0.0.0:9000 ...")
    # 8) Start the WebSocket server on port 9000
    async with serve(process_message, "0.0.0.0", 9000):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
