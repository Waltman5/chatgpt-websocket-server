import asyncio
import json
import os
import requests
from websockets import serve

# Get Hugging Face API key from Render's environment variables
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Define Hugging Face API URL
API_URL = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"

# Set headers
HEADERS = {
    "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
    "Content-Type": "application/json"
}

async def process_message(websocket, path):
    async for data in websocket:
        try:
            conversation = json.loads(data)  # Parse incoming JSON
            user_message = conversation[-1]["content"]  # Extract last user message

            # Make API request to Hugging Face
            payload = {"inputs": user_message}
            response = requests.post(API_URL, headers=HEADERS, json=payload)

            # Check API response
            if response.status_code == 200:
                reply = response.json()[0]["generated_text"]
            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                reply = f"Error {response.status_code}: {response.text}"

            await websocket.send(reply)

        except Exception as e:
            error_msg = f"⚠️ Error: {str(e)}"
            print(error_msg)
            await websocket.send(error_msg)

async def main():
    print("✅ WebSocket server is starting on ws://0.0.0.0:9000 ...")
    async with serve(process_message, "0.0.0.0", 9000):
        await asyncio.Future()  # Keep server running

if __name__ == "__main__":
    asyncio.run(main())
