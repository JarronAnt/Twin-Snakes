import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import sys

def main():
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY"   )

    client = genai.Client(api_key=api_key)

    chat = client.chats.create   (
        model="gemini-3-flash-preview",
        config=types.GenerateContentConfig(
            system_instruction="""
You are Grog, a witty Caveman.
You explain things simply, straightforward, keep responses short and speak like a caveman.
You have dry humor and are sarcastic but never rude.
""",
            thinking_config=types.ThinkingConfig( thinking_budget=0))
    )
   
    print("Chat started. Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() in ["exit", "quit"]:
            break

        response = chat.send_message(user_input)

        print("\nGrog:")
        print(response.text)

        if response.usage_metadata:
            print("\n--- Token Usage ---")
            print(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
            print(f"Response tokens: {response.usage_metadata.candidates_token_count}")
            print()
    

main()
