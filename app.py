import asyncio
import json
import os
import requests
from time import sleep
from websockets import serve, exceptions

# Get Hugging Face API key
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Hugging Face API URL
API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"

# Set headers
HEADERS = {
    "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
    "Content-Type": "application/json"
}

async def process_message(websocket, path):
    async for data in websocket:
        try:
            conversation = json.loads(data)  # Parse JSON input
            user_message = conversation[-1]["content"]  # Extract last user message
            
            # Prepare API request
            payload = {
                "inputs": user_message,
                "parameters": {
                    "max_length": 200,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }

            # Make request to Hugging Face
            response = requests.post(API_URL, headers=HEADERS, json=payload)

            # Handle 503 error (model is loading)
            if response.status_code == 503:
                error_data = response.json()
                estimated_time = error_data.get("estimated_time", 30)
                print(f"⚠️ Model is loading, retrying in {estimated_time} seconds...")

                # Notify user and wait before retrying
                try:
                    await websocket.send(f"⏳ Model is loading, please wait {int(estimated_time)} seconds...")
                except exceptions.ConnectionClosedOK:
                    print("⚠️ Client disconnected before receiving response.")
                    return  # Stop execution if client disconnects

                sleep(int(estimated_time) + 1)
                response = requests.post(API_URL, headers=HEADERS, json=payload)

            # Check API response
            if response.status_code == 200:
                reply_data = response.json()
                if isinstance(reply_data, list) and "generated_text" in reply_data[0]:
                    reply = reply_data[0]["generated_text"]
                else:
                    reply = "⚠️ Unexpected response format."
            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                reply = f"Error {response.status_code}: {response.text}"

            # Send response to client (handle disconnections)
            try:
                await websocket.send(reply)
            except exceptions.ConnectionClosedOK:
                print("⚠️ Client disconnected before receiving response.")
                return  # Stop execution if client disconnects

        except Exception as e:
            print(f"⚠️ Error: {str(e)}")
            try:
                await websocket.send(f"⚠️ Error: {str(e)}")
            except exceptions.ConnectionClosedOK:
                print("⚠️ Client disconnected before receiving error message.")
                return  # Stop execution if client disconnects

async def main():
    print("✅ WebSocket server is running on ws://0.0.0.0:9000 ...")
    async with serve(process_message, "0.0.0.0", 9000):
        await asyncio.Future()  # Keep server running

if __name__ == "__main__":
    asyncio.run(main())
