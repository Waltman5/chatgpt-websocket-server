import asyncio
import json
import os
from websockets import serve, exceptions
from dotenv import load_dotenv
from notdiamond import NotDiamond

# Load environment variables from .env
load_dotenv()

# Retrieve your NotDiamond API key from the environment
NOTDIAMOND_API_KEY = os.getenv("NOTDIAMOND_API_KEY")

if not NOTDIAMOND_API_KEY:
    print("⚠️  WARNING: The environment variable 'NOTDIAMOND_API_KEY' is not set.")
    print("    Please check your .env file or set the variable manually.")
    import sys
    sys.exit(1)
else:
    print("✅ Found NotDiamond API key in 'NOTDIAMOND_API_KEY' environment variable.")

# Initialize the NotDiamond client with your key
client = NotDiamond(api_key=NOTDIAMOND_API_KEY)

async def process_message(websocket, path):
    async for data in websocket:
        try:
            conversation = json.loads(data)
            user_message = conversation[-1]["content"].strip()

            # Create a chat completion via NotDiamond using only free models
            result, usage_info, provider = client.chat.completions.create(
                messages=[{"role": "user", "content": user_message}],
                model=[
                    "perplexity/llama-3.1-sonar-large-128k-online",
                    "mistral/mistral-7b-instruct",
                    "cohere/command-r-plus"
                ],
                exclude_providers=["openai"],  # Explicitly exclude OpenAI
                tradeoff='cost'  # Optimize based on cost vs. performance
            )

            print("LLM called:", provider.model)
            reply = result.content or "⚠️ Sorry, I couldn't generate a response."
            print("LLM output:", reply)

            await websocket.send(reply)

        except Exception as e:
            print(f"⚠️ Error in process_message: {e}")
            try:
                await websocket.send(f"⚠️ Error: {e}")
            except exceptions.ConnectionClosedOK:
                print("Client disconnected before receiving error message.")
            return

async def main():
    PORT = int(os.getenv("PORT", 9000))
    print(f"✅ WebSocket server is running on ws://0.0.0.0:{PORT} ...")
    async with serve(process_message, "0.0.0.0", PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
