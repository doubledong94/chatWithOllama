from flask import Flask, render_template, request, jsonify, Response, redirect, url_for, session
from call_ollama import print_user_message, print_assistant_message
import warnings
import json, sys
import threading
import requests
import datetime
import os

# Suppress UserWarnings
warnings.filterwarnings("ignore", category=UserWarning)

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a strong random key

# Global variable to store conversation history
conversation_history = []
MODEL_NAME = "qwq:32b"  # Default model name, you can change it here
MODEL_LIST = []

PASSWORD = "ydd94"  # Set the password here

# Global variable to control stream termination
stream_active = False
stream_stop_event = threading.Event()

# Directory to store chat history
CHAT_HISTORY_DIR = "chat_history"
if not os.path.exists(CHAT_HISTORY_DIR):
    os.makedirs(CHAT_HISTORY_DIR)

# Global variable to store the filepath of the loaded history
loaded_history_filepath = None

# Counter for the number of conversations today
conversation_counter = 0


def save_conversation_to_file(conversation_history, filepath=None):
    """Saves the conversation history to a text file."""
    global conversation_counter
    if filepath is None:
        now = datetime.datetime.now()
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M%S")

        # find how many file already exist in this day
        file_count_today = 0
        for filename in os.listdir(CHAT_HISTORY_DIR):
            if filename.startswith(date_str):
                file_count_today += 1

        conversation_counter = file_count_today + 1
        filename = f"{date_str}-{time_str}-conversation-{conversation_counter}.txt"
        filepath = os.path.join(CHAT_HISTORY_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        for message in conversation_history:
            role = message["role"]
            content = message["content"]
            f.write(f"{role}: {content}\n")
            if role == 'assistant':
                f.write("\n-----------------------------------------------------------------------------------------\n\n")
    print(f"Conversation saved to {filepath}")


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles the login page."""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Incorrect password')
    else:
        return render_template('login.html')


@app.before_request
def before_request():
    """Checks if the user is logged in before each request."""
    if request.endpoint not in ('login', 'static') and not session.get('logged_in'):
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    """Handles the logout."""
    session.pop('logged_in', None)
    return redirect(url_for('login'))


@app.route("/")
def index():
    """Renders the main page with the chat interface."""
    return render_template("index.html")


def generate_chat_stream(model_name, messages):
    """
    Generates a stream of chat responses from Ollama.

    Args:
        model_name: The name of the Ollama model to use.
        messages: The list of conversation messages.

    Yields:
        JSON-encoded strings representing each chunk of the assistant's response.
    """
    global stream_active
    global stream_stop_event
    url = "http://localhost:11434/api/chat"
    data = {
        "model": model_name,
        "messages": messages,
        "stream": True
    }
    headers = {"Content-Type": "application/json"}

    global MODEL_NAME
    global conversation_history
    stream_active = True
    stream_stop_event.clear()  # Reset the event

    try:
        import requests
        response = requests.post(url, data=json.dumps(data), headers=headers, stream=True)
        response.raise_for_status()

        assistant_response = ""  # store the assistant response in all
        conversation_history.append(
            {"role": "assistant", "content": assistant_response})  # add all response to history
        for line in response.iter_lines():
            if stream_stop_event.is_set():
                print("Stream stopped by user.")
                yield f"data: {json.dumps({'end': True})}\n\n"
                return
            if line:
                decoded_line = line.decode("utf-8")
                json_data = json.loads(decoded_line) if decoded_line.startswith('{') else {}
                text_chunk = json_data.get("message", {}).get("content", "")
                assistant_response += text_chunk  # add the text_chunk to all response
                conversation_history[-1]['content'] = assistant_response
                sys.stdout.write(text_chunk)
                sys.stdout.flush()
                yield f"data: {json.dumps({'response': text_chunk})}\n\n"
                if json_data.get('done', False):
                    yield f"data: {json.dumps({'end': True})}\n\n"
                    break

    except requests.exceptions.RequestException as e:
        yield f"data: {json.dumps({'error': f'Request error: {e}', 'end': True})}\n\n"
    except json.JSONDecodeError as e:
        yield f"data: {json.dumps({'error': f'JSON decode error: {e}', 'end': True})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': f'An error occurred: {e}', 'end': True})}\n\n"
    finally:
        stream_active = False
        stream_stop_event.clear()


@app.route("/select_model", methods=["POST"])
def select_model():
    """Receives the selected model name from the client and updates MODEL_NAME."""
    global MODEL_NAME
    try:
        data = request.get_json()
        new_model = data.get("model")
        if new_model in MODEL_LIST:
            MODEL_NAME = new_model
            print(f"Model changed to: {MODEL_NAME}")  # Optional: Log the change
            return jsonify({"message": "Model updated successfully."}), 200
        else:
            return jsonify({"error": "Model not exist"}), 400

    except Exception as e:
        print(f"Error in /select_model: {e}")
        return jsonify({"error": "An error occurred"}), 500


@app.route("/chat", methods=["POST"])
def chat():
    """Handles chat messages and returns the assistant's response."""
    global conversation_history
    global MODEL_NAME

    try:
        data = request.get_json()
        user_prompt = data.get("message")
        print_user_message(user_prompt)
        conversation_history.append({"role": "user", "content": user_prompt})

        def generate():
            for chunk in generate_chat_stream(MODEL_NAME, conversation_history):
                yield chunk
            yield "data: {}\n\n"

        return Response(generate(), mimetype="text/event-stream")

    except Exception as e:
        print(f"Error in /chat: {e}")
        return jsonify({"error": "An error occurred"}), 500


@app.route("/stop", methods=["POST"])
def stop_generate():
    """Stops the stream generation."""
    global stream_active
    global stream_stop_event
    if stream_active:
        stream_stop_event.set()
        return jsonify({"message": "Stream stopping"}), 200
    else:
        return jsonify({"message": "No stream active"}), 200


@app.route("/models", methods=["GET"])
def get_models():
    """Get the available models."""
    global MODEL_LIST

    if not MODEL_LIST:
        import requests
        url = "http://localhost:11434/api/tags"
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            json_data = json.loads(response.text)
            model_list = [tag.get("name") for tag in json_data.get("models", [])]
            model_list.sort()
            MODEL_LIST = model_list
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({"error": "An error occurred"}), 500
    return jsonify(MODEL_LIST)


@app.route("/reset", methods=["POST"])
def reset_chat():
    """Resets the conversation history."""
    global conversation_history
    global loaded_history_filepath

    if conversation_history:
        save_conversation_to_file(conversation_history, loaded_history_filepath)

    conversation_history = []
    # Reset the loaded filepath
    loaded_history_filepath = None
    return jsonify({"message": "Chat history reset."})


@app.route("/history", methods=["GET"])
def get_history():
    """Return the current conversation history."""
    global conversation_history
    return jsonify(conversation_history)


@app.route("/current_model", methods=["GET"])
def get_current_model():
    """Return the current select model"""
    global MODEL_NAME
    return jsonify({"current_model": MODEL_NAME})

@app.route("/chat_history_list", methods=["GET"])
def chat_history_list():
    """Returns a list of available chat history files."""
    history_files = []
    for filename in os.listdir(CHAT_HISTORY_DIR):
        if filename.endswith(".txt"):
            history_files.append(filename)
    history_files.sort()
    return jsonify(history_files)

@app.route("/load_chat_history", methods=["POST"])
def load_chat_history():
    """Loads a specific chat history file and updates the current conversation."""
    global conversation_history
    global loaded_history_filepath
    try:
        data = request.get_json()
        filename = data.get("filename")
        filepath = os.path.join(CHAT_HISTORY_DIR, filename)

        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"}), 404

        conversation_history = []  # Clear current history
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
            i = 0
            while i < len(lines):
                line = lines[i]
                if line.startswith("user: "):
                    content = line[6:]
                    conversation_history.append({"role": "user", "content": content.strip()})
                    i += 1
                elif line.startswith("assistant: "):
                    content = ""
                    while i < len(lines) and not lines[i].startswith('---------------------------------------------------------------------------------------'):
                        content+= lines[i]
                        i += 1
                    conversation_history.append({"role": "assistant", "content": content[11:].strip()})
                    i += 2  # Skip separator and empty lines

                else:
                    i += 1
        # Store the filepath after loading
        loaded_history_filepath = filepath
        return jsonify({"message": "Chat history loaded", "history": conversation_history})

    except Exception as e:
        print(f"Error loading chat history: {e}")
        return jsonify({"error": "An error occurred while loading history"}), 500

if __name__ == "__main__":
    app.run(debug=True)
