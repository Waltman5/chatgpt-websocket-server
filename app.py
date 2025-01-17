import asyncio
import json
import os
import requests
import re
from time import sleep
from websockets import serve, exceptions

# Get Hugging Face API key
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Hugging Face API URL (Using Falcon 7B-Instruct)
API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"

# Set headers
HEADERS = {
    "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
    "Content-Type": "application/json"
}

async def process_message(websocket, path):
    async for data in websocket:
        try:
            conversation = json.loads(data)
            user_message = conversation[-1]["content"].strip()

            # Define max_tokens dynamically
            input_length = len(user_message.split())
            if input_length <= 3:
                max_tokens = 30
            elif input_length <= 10:
                max_tokens = 100
            else:
                max_tokens = 250

            # **Better Prompt Formatting**
            formatted_prompt = f"""
### Instruction:
You are a cryptocurrency expert. Answer clearly and concisely.
Do NOT repeat the user’s input.
Do NOT introduce yourself.
Only provide the answer.

### User:
{user_message}

### AI:
"""

            payload = {
                "inputs": formatted_prompt,
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "repetition_penalty": 1.2
                }
            }

            # **Make request to Hugging Face**
            response = requests.post(API_URL, headers=HEADERS, json=payload)

            # **Handle 503 error (Model Loading)**
            if response.status_code == 503:
                error_data = response.json()
                estimated_time = error_data.get("estimated_time", 30)
                print(f"⚠️ Model is loading, retrying in {estimated_time} seconds...")

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
                print("📝 RAW RESPONSE:", reply_data)  # DEBUG LOGGING

                if isinstance(reply_data, list) and "generated_text" in reply_data[0]:
                    raw_reply = reply_data[0]["generated_text"]

                    # **CLEAN AI RESPONSE**
                    reply = re.sub(r"^.*?AI: ", "", raw_reply).strip()
                    reply = re.sub(r"### Instruction:.*", "", reply, flags=re.DOTALL).strip()
                    reply = re.sub(r"### User:.*", "", reply, flags=re.DOTALL).strip()

                    if not reply:  # **Handle Empty Response**
                        reply = "⚠️ Sorry, I couldn't generate a response."

                else:
                    reply = "⚠️ Unexpected response format."

            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                reply = f"Error {response.status_code}: {response.text}"

            print("📢 FINAL RESPONSE:", reply)  # DEBUG LOGGING

            # **Send Response to Client**
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
