import asyncio
import json
import os
import websockets
from websockets import serve, exceptions

# ✅ 1) Import dotenv to load environment variables
from dotenv import load_dotenv
from notdiamond import NotDiamond

# ✅ 2) Load environment variables from .env
load_dotenv()

# ✅ 3) Read your NotDiamond API key from the .env file
NOTDIAMOND_API_KEY = os.getenv("onboarding")

if not NOTDIAMOND_API_KEY:
    print("⚠️  WARNING: The environment variable 'onboarding' is not set.")
    print("    Please check your .env file or set the variable manually.")
    # Optionally exit the script if API key is required
    import sys
    sys.exit(1)
else:
    print("✅ Found NotDiamond API key in 'onboarding' environment variable.")

# ✅ 4) Initialize the NotDiamond client with your key
client = NotDiamond(api_key=NOTDIAMOND_API_KEY)

async def process_message(websocket, path):
    async for data in websocket:
        try:
            # ✅ 5) Parse the received message
            conversation = json.loads(data)
            user_message = conversation[-1]["content"].strip()

            # ✅ 6) Create a chat completion via NotDiamond
            result, usage_info, provider = client.chat.completions.create(
                messages=[{"role": "user", "content": user_message}],
                model=[
                    "perplexity/llama-3.1-sonar-large-128k-online",  # ✅ Free
                    "mistral/mistral-7b-instruct",                   # ✅ Free
                    "cohere/command-r-plus"                          # ✅ Free
                ],
                exclude_providers=["openai"],  # ❌ Force NotDiamond to avoid OpenAI
                tradeoff='cost'  # Uses the best free model based on cost vs. performance
            )

            # ✅ 7) Debug logs
            print("LLM called:", provider.model)  # Log model used
            reply = result.content
            if not reply:
                reply = "⚠️ Sorry, I couldn't generate a response."
            print("LLM output:", reply)

            # ✅ 8) Send the response back to the client
            await websocket.send(reply)

        except Exception as e:
            print(f"⚠️ Error in process_message: {e}")
            try:
                await websocket.send(f"⚠️ Error: {e}")
            except exceptions.ConnectionClosedOK:
                print("Client disconnected before receiving error message.")
            return



            # ✅ 7) Debug logs
            print("LLM called:", provider.model)  # Log model used
            reply = result.content
            if not reply:
                reply = "⚠️ Sorry, I couldn't generate a response."
            print("LLM output:", reply)

            # ✅ 8) Send the response back to the client
            await websocket.send(reply)

        except Exception as e:
            print(f"⚠️ Error in process_message: {e}")
            try:
                await websocket.send(f"⚠️ Error: {e}")
            except exceptions.ConnectionClosedOK:
                print("Client disconnected before receiving error message.")
            return

async def main():
    PORT = int(os.getenv("PORT", 9000))  # Use Render's assigned PORT
    print(f"✅ WebSocket server is running on ws://0.0.0.0:{PORT} ...")
    
    async with serve(process_message, "0.0.0.0", PORT):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())
