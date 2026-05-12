import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

def main():
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY"   )

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content   (
        model="gemini-3-flash-preview",
        contents="Why is the sky blue?",
        config=types.GenerateContentConfig(
            system_instruction="""
You are Grog, a witty Caveman.
You explain things simply, straightforward, keep responses short and speak like a caveman.
You have dry humor and are sarcastic but never rude.
""",
            thinking_config=types.ThinkingConfig( thinking_budget=0))
    )
    print(response.text)
    if response is None or response.usage_metadata is None:
        return

    print(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
    print(f"Response tokens: {response.usage_metadata.candidates_token_count}")

main()
