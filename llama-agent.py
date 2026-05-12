import os
import json
import requests
from dotenv import load_dotenv

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
        return f"Unknown tool: {name}"

    return tool_map[name](**(args or {}))

# =========================================================
# OLLAMA CONFIG
# =========================================================

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3"

def call_llm(messages):
    r = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": messages,
            "stream": False
        }
    )
    r.raise_for_status()
    return r.json()["message"]["content"]

# =========================================================
# TOOL PARSER (HIDDEN PROTOCOL)
# =========================================================

def parse_tool_call(text):
    """
    Looks for:
    <tool:name>{json}</tool>
    """
    if "<tool:" not in text:
        return None

    try:
        start_tag = text.index("<tool:") + 6
        end_tag = text.index(">", start_tag)

        tool_name = text[start_tag:end_tag].strip()

        json_start = end_tag + 1
        json_end = text.index("</tool>", json_start)

        json_str = text[json_start:json_end].strip()

        args = json.loads(json_str)

        return tool_name, args

    except Exception:
        return None

# =========================================================
# MAIN LOOP
# =========================================================

def main():
    load_dotenv()

    print("\nGrog awake (clean Ollama mode). Type 'exit' to quit.\n")

    messages = [
        {
            "role": "system",
            "content": (
                "You are Grog, a caveman coding agent.\n\n"
                "You can use tools internally.\n"
                "NEVER show tool syntax to the user.\n\n"
                "To use a tool, output EXACTLY this format:\n"
                "<tool:tool_name>{...json args...}</tool>\n\n"
                "Available tools:\n"
                "- list_files\n"
                "- walk_directory\n"
                "- find (name, path)\n"
                "- read_file (path)\n"
                "- write_file (path, content)\n"
                "- append_file (path, content)\n"
                "- delete_file (path)\n\n"
                "Rules:\n"
                "- Never show JSON or tool syntax to user\n"
                "- If not using tools, respond normally\n"
                "- Be short, caveman style\n"
            )
        }
    ]

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            break

        messages.append({"role": "user", "content": user_input})

        while True:
            reply = call_llm(messages)

            tool = parse_tool_call(reply)

            # =====================================================
            # TOOL EXECUTION PATH
            # =====================================================
            if tool:
                name, args = tool

                print(f"\n[Tool] {name} {args}")

                result = run_tool(name, args)

                print(f"\n[Result]\n{result}")

                # feed tool result back (hidden from user)
                messages.append({"role": "assistant", "content": reply})
                messages.append({"role": "tool", "content": str(result)})

                continue

            # =====================================================
            # FINAL ANSWER PATH
            # =====================================================
            messages.append({"role": "assistant", "content": reply})

            print("\nGrog:", reply)
            break

        print()

if __name__ == "__main__":
    main()
