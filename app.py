import asyncio
import json
import os
import requests
import re
from time import sleep
import websockets
from websockets import serve, exceptions

# Get Hugging Face API key from environment
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# -- Recommended: Check if the API key is missing/invalid
if not HUGGINGFACE_API_KEY:
    print("⚠️  HUGGINGFACE_API_KEY is not set. Please set it before running.")
    # You can exit here if needed:
    # import sys
    # sys.exit(1)

# Hugging Face API URL (Using Falcon 7B-Instruct or any other model)
API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"

HEADERS = {
    "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
    "Content-Type": "application/json"
}

async def process_message(websocket, path):
    async for data in websocket:
        try:
            conversation = json.loads(data)
            user_message = conversation[-1]["content"].strip()

            # -- Dynamically decide max tokens
            input_length = len(user_message.split())
            if input_length <= 3:
                max_tokens = 30
            elif input_length <= 10:
                max_tokens = 100
            else:
                max_tokens = 250

            # -- Prompt (simplified to avoid removing all text)
            # Adjust or translate the instruction as desired
            formatted_prompt = f"""
You are a helpful cryptocurrency expert. Answer the user's question clearly and concisely, in a polite tone.

User: {user_message}
AI:
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

            # Make request to Hugging Face
            response = requests.post(API_URL, headers=HEADERS, json=payload)

            # Handle 503 (model loading)
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

            # Check API response
            if response.status_code == 200:
                reply_data = response.json()
                print("📝 RAW RESPONSE:", reply_data)  # Debug logging

                # The HF Inference API typically returns a list of dicts
                # e.g. [{"generated_text": "..."}]
                if isinstance(reply_data, list) and "generated_text" in reply_data[0]:
                    raw_reply = reply_data[0]["generated_text"]

                    # -- Minimal Cleanup:
                    # If Falcon’s text starts with the entire prompt repeated, we can remove it.
                    # But do so carefully. Example:
                    reply = raw_reply.replace(formatted_prompt, "").strip()

                    # Some Falcon outputs include partial repeated instructions or 'User:' lines.
                    # You can remove them more gently:
                    # We'll remove any leading "AI:" or leftover "User:" lines:
                    reply = re.sub(r"^(AI:|User:)\s*", "", reply)

                    # If the result is empty, fallback:
                    if not reply:
                        reply = "⚠️ Sorry, I couldn't generate a response."
                else:
                    reply = "⚠️ Unexpected response format."

            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                reply = f"Error {response.status_code}: {response.text}"

            print("📢 FINAL RESPONSE:", reply)  # Debug logging

            # Send final response
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
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
