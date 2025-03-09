from flask import Flask, render_template, request, jsonify, Response, redirect, url_for, session
from call_ollama import print_user_message, print_assistant_message
import warnings
import json, sys

# Suppress UserWarnings
warnings.filterwarnings("ignore", category=UserWarning)

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a strong random key

# Global variable to store conversation history
conversation_history = []
MODEL_NAME = "qwq:32b"  # Default model name, you can change it here
MODEL_LIST = []

PASSWORD = "ydd94"  # Set the password here


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
    url = "http://localhost:11434/api/chat"
    data = {
        "model": model_name,
        "messages": messages,
        "stream": True
    }
    headers = {"Content-Type": "application/json"}

    global MODEL_NAME
    global conversation_history
    try:
        import requests
        response = requests.post(url, data=json.dumps(data), headers=headers, stream=True)
        response.raise_for_status()

        assistant_response = "" #store the assistant response in all
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode("utf-8")
                json_data = json.loads(decoded_line) if decoded_line.startswith('{') else {}
                text_chunk = json_data.get("message", {}).get("content", "")
                assistant_response += text_chunk # add the text_chunk to all response
                sys.stdout.write(text_chunk)
                text_chunk = text_chunk.replace('\n', '<br>')
                sys.stdout.flush()
                yield f"data: {json.dumps({'response': text_chunk})}\n\n"
                if json_data.get('done', False):
                    conversation_history.append({"role": "assistant", "content": assistant_response}) # add all response to history
                    break

    except requests.exceptions.RequestException as e:
        yield f"data: {json.dumps({'error': f'Request error: {e}', 'end': True})}\n\n"
    except json.JSONDecodeError as e:
        yield f"data: {json.dumps({'error': f'JSON decode error: {e}', 'end': True})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': f'An error occurred: {e}', 'end': True})}\n\n"

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

        return Response(generate(), mimetype="text/event-stream")

    except Exception as e:
        print(f"Error in /chat: {e}")
        return jsonify({"error": "An error occurred"}), 500

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
    conversation_history = []
    return jsonify({"message": "Chat history reset."})



if __name__ == "__main__":
    app.run(debug=True)