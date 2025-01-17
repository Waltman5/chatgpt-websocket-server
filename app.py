import asyncio
import json
import os
import requests
from websockets import serve

# Get Hugging Face API key from environment variables
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Hugging Face API endpoint
API_URL = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"

# Set headers for Hugging Face API requests
HEADERS = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}

async def process_message(websocket, path):
    async for data in websocket:
        try:
            conversation = json.loads(data)  # Parse incoming JSON
            user_message = conversation[-1]["content"]  # Extract last user message

            # Send request to Hugging Face API
            response = requests.post(API_URL, headers=HEADERS, json={"inputs": user_message})

            if response.status_code == 200:
                reply = response.json().get("generated_text", "Sorry, I couldn't understand that.")
            else:
                reply = "Error communicating with Hugging Face API."

            await websocket.send(reply)
        
        except Exception as e:
            await websocket.send(f"Error: {str(e)}")

async def main():
    print("✅ WebSocket server is starting on ws://0.0.0.0:9000 ...")
    async with serve(process_message, "0.0.0.0", 9000):
        await asyncio.Future()  # Keep the server running

if __name__ == "__main__":
    asyncio.run(main())
