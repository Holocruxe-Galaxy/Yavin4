from flask import Flask, request, jsonify
from flask_cors import CORS
from main import generate_response, store_in_db
import sys
import sqlite3

print("Using Python at:", sys.executable)
print("Python version:", sys.version)

app = Flask(__name__)
CORS(app)

@app.route('/chat', methods=['POST'])
def chat():
    print("Chat endpoint hit")
    message = request.json.get('message')
    print(f"Received message: {message}")

    if not message:
        print("No message found in the request.")
        return jsonify({"error": "No message provided"}), 400

    try:
        response = generate_response(message, txt_filepath='data.txt')
        print(f"Generated response: {response}")
        return jsonify(response=response)
    except Exception as e:
        print(f"Error during response generation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/store', methods=['POST'])
def store():
    data = request.json
    question = data['question']
    answer = data['answer']

    with sqlite3.connect('personal_assistant.db') as conn:
        cursor = conn.cursor()
        store_in_db(conn, cursor, question, answer)

    return jsonify(message="Stored successfully")

if __name__ == "__main__":
    app.run(port=5000)
