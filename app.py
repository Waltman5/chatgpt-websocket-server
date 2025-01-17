import asyncio
import json
import os
import requests
from websockets import serve

# Get Hugging Face API key from environment variables
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Define the Hugging Face API endpoint
API_URL = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"

# Set headers for Hugging Face API requests
HEADERS = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}

async def process_message(websocket):
    async for data in websocket:
        conversation = [{"role": msg[0], "content": msg[1]} for msg in json.loads(data)]

        # Send request to Hugging Face API
        response = requests.post(API_URL, headers=HEADERS, json={"inputs": conversation[-1]["content"]})
        
        if response.status_code == 200:
            reply = response.json().get("generated_text", "Sorry, I couldn't understand that.")
        else:
            reply = "Error communicating with Hugging Face API."

        await websocket.send(reply)

async def main():
    async with serve(process_message, "0.0.0.0", 9000):
        await asyncio.Future()  # Keep the server running

if __name__ == "__main__":
    asyncio.run(main())
