import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
from main import generate_response
from main import store_in_db


app = Flask(__name__)
CORS(app)

@app.route('/chat', methods=['POST'])
def chat():
    message = request.json['message']
    response = generate_response(message)
    return jsonify(response=response)

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
