import os
import sys
import json
from pathlib import Path

from dotenv import load_dotenv
from google import genai

BASE_DIR = Path(__file__).resolve().parent
HISTORY_FILE = BASE_DIR / "chat_history.json"
load_dotenv(BASE_DIR / ".env")

DEFAULT_MODELS = (
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
)
EXIT_COMMANDS = {"exit", "quit", "q"}
CLEAR_COMMANDS = {"/clear", "clear memory"}


def get_api_key():
    api_key = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")

    if not api_key or api_key.startswith("YOUR_"):
        print("No valid GEMINI_API_KEY found.")
        print(f"Add your Gemini API key to: {BASE_DIR / '.env'}")
        return None

    return api_key


def get_model_candidates():
    env_model = os.getenv("GEMINI_MODEL", "").strip()
    return tuple(dict.fromkeys((env_model, *DEFAULT_MODELS) if env_model else DEFAULT_MODELS))


def add_message(history, role, text):
    history.append(
        {
            "role": role,
            "parts": [{"text": text}],
        }
    )


def load_history():
    if not HISTORY_FILE.exists():
        return []

    try:
        with HISTORY_FILE.open("r", encoding="utf-8") as file:
            history = json.load(file)
    except (OSError, json.JSONDecodeError):
        print("Could not read chat history. Starting with empty memory.")
        return []

    if not isinstance(history, list):
        print("Chat history has an invalid format. Starting with empty memory.")
        return []

    return history


def save_history(history):
    try:
        with HISTORY_FILE.open("w", encoding="utf-8") as file:
            json.dump(history, file, indent=2)
    except OSError as exc:
        print(f"Could not save chat history: {exc}")


def clear_history(history):
    history.clear()
    try:
        HISTORY_FILE.unlink(missing_ok=True)
    except OSError as exc:
        print(f"Could not delete chat history: {exc}")


def generate_reply(client, models, history):
    last_error = None
    for model in models:
        try:
            response = client.models.generate_content(
                model=model,
                contents=history,
            )
            return model, response.text or str(response)
        except Exception as exc:
            last_error = exc
            print(f"Model failed: {model} ({type(exc).__name__})")

    raise RuntimeError(f"{type(last_error).__name__}: {last_error}") from last_error


def print_error(error):
    print("\nRequest failed for all configured models.")
    print(error)
    print("Check your API key, quota, billing status, rate limits, and model name.")


def run_chat(client, models, first_prompt=""):
    history = load_history()
    active_model = models[0]
    saved_turns = len(history) // 2

    print("Gemini Chat CLI")
    print(f"Model: {active_model}")
    print(f"Memory: {saved_turns} saved conversation turns")
    print("Type exit, quit, or q to stop. Type /clear to reset memory.\n")

    prompt = first_prompt
    while True:
        if not prompt:
            prompt = input("You: ").strip()

        if not prompt:
            continue

        if prompt.lower() in EXIT_COMMANDS:
            print("Goodbye.")
            return

        if prompt.lower() in CLEAR_COMMANDS:
            clear_history(history)
            print("Memory cleared.\n")
            prompt = ""
            continue

        add_message(history, "user", prompt)

        try:
            active_model, reply = generate_reply(client, models, history)
        except RuntimeError as exc:
            history.pop()
            print_error(exc)
            prompt = ""
            continue

        add_message(history, "model", reply)
        save_history(history)
        print(f"\nGemini ({active_model}): {reply}\n")
        prompt = ""


def main():
    api_key = get_api_key()
    if not api_key:
        return

    client = genai.Client(api_key=api_key)
    models = get_model_candidates()
    first_prompt = " ".join(sys.argv[1:]).strip()
    run_chat(client, models, first_prompt)


if __name__ == "__main__":
    main()
