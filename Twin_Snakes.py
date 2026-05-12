import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# =========================================================
# FILE SYSTEM TOOLS
# =========================================================

def list_files(path="."):
    return os.listdir(path)

def walk_directory(path="."):
    output = []
    for root, dirs, files in os.walk(path):
        output.append(f"\n[{root}]")
        for d in dirs:
            output.append(f"DIR  - {d}")
        for f in files:
            output.append(f"FILE - {f}")
    return "\n".join(output)

def find(name="", path="."):
    search_roots = [path]

    if path == ".":
        search_roots.append(os.path.expanduser("~/Desktop"))
        search_roots.append(os.path.expanduser("~/Documents"))

    matches = []

    for root_path in search_roots:
        if not os.path.exists(root_path):
            continue

        for root, dirs, files in os.walk(root_path):
            for d in dirs:
                if name.lower() in d.lower():
                    matches.append(os.path.join(root, d))

            for f in files:
                if name.lower() in f.lower():
                    matches.append(os.path.join(root, f))

    return matches if matches else "No matches found"

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Written: {path}"

def append_file(path, content):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(content)
    return f"Appended: {path}"

def delete_file(path):
    os.remove(path)
    return f"Deleted: {path}"

# =========================================================
# TOOL ROUTER
# =========================================================

def run_tool(name, args):
    tool_map = {
        "list_files": list_files,
        "walk_directory": walk_directory,
        "find": find,
        "read_file": read_file,
        "write_file": write_file,
        "append_file": append_file,
        "delete_file": delete_file,
    }

    if name not in tool_map:
        return "Unknown tool"

    return tool_map[name](**(args or {}))

# =========================================================
# MAIN
# =========================================================

def main():
    load_dotenv()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    client = genai.Client(api_key=api_key)

    tools = [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="list_files",
                    description="List files in a directory",
                    parameters={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"}
                        },
                    },
                ),
                types.FunctionDeclaration(
                    name="walk_directory",
                    description="Recursively explore directories",
                    parameters={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"}
                        },
                    },
                ),
                types.FunctionDeclaration(
                    name="find",
                    description="Search files/folders by name",
                    parameters={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "path": {"type": "string"}
                        },
                        "required": ["name"]
                    },
                ),
                types.FunctionDeclaration(
                    name="read_file",
                    description="Read file contents",
                    parameters={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"}
                        },
                        "required": ["path"]
                    },
                ),
                types.FunctionDeclaration(
                    name="write_file",
                    description="Write file contents",
                    parameters={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"}
                        },
                        "required": ["path", "content"]
                    },
                ),
                types.FunctionDeclaration(
                    name="append_file",
                    description="Append file contents",
                    parameters={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"}
                        },
                        "required": ["path", "content"]
                    },
                ),
                types.FunctionDeclaration(
                    name="delete_file",
                    description="Delete a file",
                    parameters={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"}
                        },
                        "required": ["path"]
                    },
                ),
            ]
        )
    ]

    chat = client.chats.create(
        model="gemini-3-flash-preview",
        config=types.GenerateContentConfig(
            tools=tools,
            system_instruction=(
                "You are Grog.\n"
                "A caveman coding agent who knows tech, science, math and everything else.\n\n"
                "You:\n"
                "- explore codebases\n"
                "- search files\n"
                "- read code\n"
                "- write code\n"
                "- modify projects\n\n"
                "- Knows general knowledge and is smart\n"
                "- Have dry humor\n"
                "- Answer any question give\n"
                "RULES:\n"
                "- Always use tools for file access\n"
                "- Use find if unsure where something is\n"
                "- Never guess file contents\n"
                "- Speak like caveman\n"
                "- Be short and direct"
            ),
        ),
    )

    print("Grog awake. Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            break

        response = chat.send_message(user_input)

        while True:
            if not response or not getattr(response, "candidates", None):
                print("\n[No response]")
                break

            candidate = response.candidates[0]
            content = getattr(candidate, "content", None)

            if not content:
                print("\n[No content]")
                break

            parts = getattr(content, "parts", []) or []
            tool_called = False

            for part in parts:
                text = getattr(part, "text", None)
                if text:
                    print("\nGrog:")
                    print(text)
                    continue

                function_call = getattr(part, "function_call", None)
                if function_call:
                    tool_called = True
                    name = function_call.name
                    args = dict(function_call.args or {})

                    print(f"\n[Tool] {name} {args}")

                    try:
                        result = run_tool(name, args)
                    except Exception as e:
                        result = f"Tool error: {e}"

                    print(f"\n[Result]\n{result}")

                    response = chat.send_message(
                        types.Part.from_function_response(
                            name=name,
                            response={"result": str(result)},
                        )
                    )
                    break

            if not tool_called:
                break

        print()

    response = chat.send_message(user_input)

    usage = getattr(response, "usage_metadata", None)
    if usage:
        print("\n--- tokens ---")
        print(f"prompt: {usage.prompt_token_count}")
        print(f"response: {usage.candidates_token_count}")
        print(f"total: {usage.total_token_count}")

if __name__ == "__main__":
    main()
