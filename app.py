import asyncio
import json
import os
import requests
from time import sleep
from websockets import serve, exceptions

# Get Hugging Face API key
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Hugging Face API URL (Using a Smarter Model)
API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"

# Set headers
HEADERS = {
    "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
    "Content-Type": "application/json"
}

async def process_message(websocket, path):
    async for data in websocket:
        try:
            conversation = json.loads(data)  # Parse JSON input
            user_message = conversation[-1]["content"].strip()  # Extract and clean user message

            # Dynamically adjust response length based on input length
            input_length = len(user_message.split())  # Count words
            if input_length <= 3:  
                max_tokens = 30  # Short response for greetings
            elif input_length <= 10:  
                max_tokens = 100  # Medium response for normal questions
            else:
                max_tokens = 250  # Detailed response for complex queries

            # **Improve prompt structure for better conversation**
            formatted_prompt = f"<|system|>You are a crypto expert AI. Answer factually and concisely.\n<|user|>{user_message}\n<|assistant|>"

            payload = {
                "inputs": formatted_prompt,  
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": 0.3,  
                    "top_p": 0.8,
                    "repetition_penalty": 1.2  
                }
            }

            # Make request to Hugging Face
            response = requests.post(API_URL, headers=HEADERS, json=payload)

            # **Handle 503 error (model loading)**
            if response.status_code == 503:
                error_data = response.json()
                estimated_time = error_data.get("estimated_time", 30)
                print(f"⚠️ Model is loading, retrying in {estimated_time} seconds...")

                # Notify user and wait before retrying
                try:
                    await websocket.send(f"⏳ Model is loading, please wait {int(estimated_time)} seconds...")
                except exceptions.ConnectionClosedOK:
                    print("⚠️ Client disconnected before receiving response.")
                    return  

                sleep(int(estimated_time) + 1)
                response = requests.post(API_URL, headers=HEADERS, json=payload)

            # **Check API response**
            if response.status_code == 200:
                reply_data = response.json()

                # Ensure the response format is correct
                if isinstance(reply_data, list) and "generated_text" in reply_data[0]:
                    raw_reply = reply_data[0]["generated_text"]
                    
                    # **Remove unnecessary assistant text**
                    if "<|assistant|>" in raw_reply:
                        reply = raw_reply.split("<|assistant|>")[-1].strip()
                    else:
                        reply = raw_reply.strip()  

                else:
                    reply = "⚠️ Unexpected response format."

            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                reply = f"Error {response.status_code}: {response.text}"

            # **Send response to client (handle disconnections)**
            try:
                await websocket.send(reply)
            except exceptions.ConnectionClosedOK:
                print("⚠️ Client disconnected before receiving response.")
                return  

        except Exception as e:
            print(f"⚠️ Error: {str(e)}")
            try:
                await websocket.send(f"⚠️ Error: {str(e)}")
            except exceptions.ConnectionClosedOK:
                print("⚠️ Client disconnected before receiving error message.")
                return  

async def main():
    print("✅ WebSocket server is running on ws://0.0.0.0:9000 ...")
    async with serve(process_message, "0.0.0.0", 9000):
        await asyncio.Future()  

if __name__ == "__main__":
    asyncio.run(main())
