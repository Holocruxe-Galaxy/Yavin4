import sqlite3
from langchain.llms import OpenAI
from dotenv import load_dotenv

load_dotenv()

def initialize_db():
    conn = sqlite3.connect('personal_assistant.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personal_info (
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    ''')
    conn.commit()
    return conn, cursor

def get_from_db(cursor, question):
    cursor.execute("SELECT answer FROM personal_info WHERE question=?", (question,))
    result = cursor.fetchone()
    return result[0] if result else None

def store_in_db(conn, cursor, question, answer):
    cursor.execute("INSERT INTO personal_info (question, answer) VALUES (?, ?)", (question, answer))
    conn.commit()

def chat_with_assistant():
    llm = OpenAI(temperature=0.5)
    conn, cursor = initialize_db()
    
    print("Personal Assistant initialized. Type 'exit' to end the chat.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
      
        db_response = get_from_db(cursor, user_input)
        if db_response:
            print("Bot (from DB):", db_response)
        else:           
            response = llm(user_input)
            print("Bot:", response)

    conn.close()
    print("Chat session ended.")

def generate_response(user_input):
    llm = OpenAI(temperature=0.5)
    
    with sqlite3.connect('personal_assistant.db') as conn:
        cursor = conn.cursor()

        db_response = get_from_db(cursor, user_input)
        if db_response:
            return db_response
        else:
            response = llm(user_input)
            store_in_db(conn, cursor, user_input, response)  
            return response


if __name__ == "__main__":
    chat_with_assistant()
