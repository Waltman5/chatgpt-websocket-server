import asyncio
import json
import os
import requests
from time import sleep
from websockets import serve

# Get Hugging Face API key from Render's environment variables
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Define Hugging Face API URL
API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"

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

            # Prepare API request payload
            payload = {
                "inputs": user_message,
                "parameters": {
                    "max_length": 200,  # Limit response length
                    "temperature": 0.7,  # Adjust creativity (lower = more factual)
                    "top_p": 0.9         # Sampling method
                }
            }

            # Make API request to Hugging Face
            response = requests.post(API_URL, headers=HEADERS, json=payload)

            # Handle 503 error (model loading)
            if response.status_code == 503:
                error_data = response.json()
                estimated_time = error_data.get("estimated_time", 30)  # Default 30 sec wait
                print(f"⚠️ Model is loading, retrying in {estimated_time} seconds...")

                # Inform user about the wait time
                await websocket.send(f"⏳ Model is loading, please wait {int(estimated_time)} seconds...")

                # Wait and retry request
                sleep(int(estimated_time) + 1)
                response = requests.post(API_URL, headers=HEADERS, json=payload)

            # Check API response
            if response.status_code == 200:
                reply_data = response.json()
                if isinstance(reply_data, list) and "generated_text" in reply_data[0]:
                    reply = reply_data[0]["generated_text"]
                else:
                    reply = "⚠️ Unexpected response format from AI."
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
