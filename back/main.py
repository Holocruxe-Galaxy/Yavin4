from fuzzywuzzy import process
import sqlite3
from langchain.llms import OpenAI
from dotenv import load_dotenv


load_dotenv()


def get_closest_match(query, choices, limit=1):
    return process.extractOne(query, choices)


def load_txt_data(filepath):
    qa_pairs = []
    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            if '::' in line:
                question, answer = line.split('::', 1)
                qa_pairs.append((question.strip(), answer.strip()))
    return qa_pairs



def get_answer(cursor, user_input, txt_qa_pairs):
    best_match, best_score = get_closest_match(user_input, [q for q, _ in txt_qa_pairs])
    if best_score >= 75:
        answer = next(a for q, a in txt_qa_pairs if q == best_match)
        return answer
    
    db_response = get_from_db(cursor, user_input)
    if db_response:
        return db_response
    
    return None




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
    cursor.execute("SELECT answer FROM personal_info WHERE question = ?", (question,))
    result = cursor.fetchone()
    return result[0] if result else None


def store_in_db(conn, cursor, question, answer):
    cursor.execute("INSERT INTO personal_info (question, answer) VALUES (?, ?)", (question, answer))
    conn.commit()

def chat_with_assistant(txt_filepath):
    llm = OpenAI(temperature=0.5)
    conn, cursor = initialize_db()
    txt_qa_pairs = load_txt_data(txt_filepath)
    
    print("Personal Assistant initialized. Type 'exit' to end the chat.")
    while True:
        user_input = input("You: ").strip()
        print(f"User input: {user_input}")  
        
        if user_input.lower() == 'exit':
            break

        txt_response = get_answer(cursor, user_input, txt_qa_pairs)
        if txt_response:
            print("Bot (from TXT):", txt_response)  
            continue
        db_response = get_from_db(cursor, user_input)
        if db_response:
            print("Bot (from DB):", db_response)  
            continue

        llm_response = llm(user_input)
        print("Bot (from LLM):", llm_response)  
        store_in_db(conn, cursor, user_input, llm_response)

    conn.close()
    print("Chat session ended.")


def generate_response(user_input, txt_filepath='data.txt'):
    try:
        llm = OpenAI(temperature=0.5)
        with sqlite3.connect('personal_assistant.db') as conn:
            cursor = conn.cursor()
            txt_qa_pairs = load_txt_data(txt_filepath)
            txt_response = get_answer(cursor, user_input, txt_qa_pairs)
            if txt_response:
                print("Bot (from TXT):", txt_response)
                return txt_response

            db_response = get_from_db(cursor, user_input)
            if db_response:
                print("Bot (from DB):", db_response)  
                return db_response

            response = llm(user_input)
            print("Bot (from LLM):", response)
            store_in_db(conn, cursor, user_input, response)
            return response
    except Exception as e:
        print(f"Error in generate_response: {e}")
        return str(e)


if __name__ == "__main__":
    chat_with_assistant('data.txt')