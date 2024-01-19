import sys
print(sys.path)
import os
from fuzzywuzzy import process, fuzz
import sqlite3
from langchain_openai import OpenAI
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
from langdetect import detect


translator = GoogleTranslator()
load_dotenv()

def get_db_response(cursor, user_input):    
    cursor.execute("SELECT question, answer FROM personal_info")
    db_qa_pairs = cursor.fetchall()
   
    db_questions = [q for q, _ in db_qa_pairs]

    best_match = get_fuzzy_match(user_input, db_questions)
    
    if best_match['score'] > 0.75:
        matched_question = best_match['text']
        answer = next((a for q, a in db_qa_pairs if q == matched_question), None)
        return answer

    return None

def get_fuzzy_match(query, questions):
    highest_score = 0
    best_match = None
    for question in questions:
        score = fuzz.token_set_ratio(query, question)
        if score > highest_score:
            highest_score = score
            best_match = question
    return {'text': best_match, 'score': highest_score / 100.0}

def translate_text(text, src_language="auto", dest_language="en"):
    try:
        translator = GoogleTranslator(source=src_language, target=dest_language)
        translation = translator.translate(text)
        print(f"Translation: '{text}' from {src_language} to {dest_language} -> '{translation}'")
        return translation
    except Exception as e:
        print(f"Error in translation: {e}")
        return f"Translation error: {e}"

def get_closest_match(query, choices):
    best_match, score = process.extractOne(query, choices)
    return {'text': best_match, 'score': score / 100.0}

def load_txt_data(filepath):
    qa_pairs = []
    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            if '::' in line:
                question, answer = line.split('::', 1)
                qa_pairs.append((question.strip(), answer.strip()))
    return qa_pairs

def get_answer(cursor, user_input, txt_qa_pairs):
    questions = [q for q, _ in txt_qa_pairs]
    best_match = get_fuzzy_match(user_input, questions)
    if best_match['score'] > 0.75:  
        matched_question = best_match['text']
        answer = next(a for q, a in txt_qa_pairs if q == matched_question)
        return answer
    return None

def initialize_db():
    db_path = 'personal_assistant.db'
    print(f"Initializing database at: {os.path.abspath(db_path)}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personal_info (
                question TEXT NOT NULL,
                answer TEXT NOT NULL
            )
        ''')
        conn.commit()
        print("Database initialized and table created.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise e 
    return conn, cursor 

def get_from_db(cursor, question):
    cursor.execute("SELECT answer FROM personal_info WHERE question = ?", (question,))
    result = cursor.fetchone()
    return result[0] if result else None

def store_in_db(conn, cursor, question, answer, txt_filepath='back/data.txt'):
   
    txt_qa_pairs = load_txt_data(txt_filepath)
    txt_questions = [q for q, _ in txt_qa_pairs]
    fuzzy_match = get_fuzzy_match(question, txt_questions)
    if fuzzy_match['score'] < 0.75:      
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

def detect_language(text):
    try:
        return detect(text)
    except Exception as e:
        print(f"Error detecting language: {e}")
        return "en" 


def generate_response(user_input, txt_filepath='data.txt', retry_attempts=3):
    target_language = 'en'
    
    source_language = detect_language(user_input)
    translated_input = user_input
    
    try:
        if source_language != target_language:
            translated_input = translate_text(user_input, src_language=source_language, dest_language=target_language)
        
        with sqlite3.connect        ('personal_assistant.db') as conn:
            cursor = conn.cursor()
            
            db_response = get_db_response(cursor, translated_input)
            if db_response:
                return translate_back_if_needed(db_response, source_language)
            
            txt_qa_pairs = load_txt_data(txt_filepath)
            txt_response = get_answer(cursor, translated_input, txt_qa_pairs)
            if txt_response:
                return translate_back_if_needed(txt_response, source_language)
            
            llm = OpenAI(temperature=0.5)
            llm_response = llm.invoke(user_input)
            store_in_db(conn, cursor, translated_input, llm_response)
            return translate_back_if_needed(llm_response, source_language)

    except Exception as e:
        print(f"Error in generate_response: {e}")
        return "An error occurred while processing your request. Please try again."


def translate_back_if_needed(response, source_language):
    target_language = 'en'
    if source_language != target_language:
        translated_response = translate_text(response, src_language=target_language, dest_language=source_language)
        return translated_response
    else:
        return response


if __name__ == "__main__":
    chat_with_assistant('back/data.txt')