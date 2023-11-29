from fuzzywuzzy import process
import sqlite3
from langchain.llms import OpenAI
from dotenv import load_dotenv
from googletrans import Translator, LANGUAGES

translator = Translator()
load_dotenv()


def translate_text(text, src_language="auto", dest_language="en"):
    try:
        # Instead of raising an error, let's just print a warning and proceed
        if dest_language not in LANGUAGES.values():
            print(f"Warning: Unsupported language code: {dest_language}. Proceeding with translation anyway.")
        
        translation = translator.translate(text, src=src_language, dest=dest_language)
        print(f"Translation: '{text}' from {src_language} to {dest_language} -> '{translation.text}'")  # Log the translation
        return translation.text
    except Exception as e:
        print(f"Error in translation: {e}")
        return f"Translation error: {e}"



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
        # Define the target language for processing (English)
        target_language = 'en'

        print(f"Original Input: {user_input}")  # Log the original input

        # Detect the language of the input
        detected_language_result = translator.detect(user_input)
        source_language = detected_language_result.lang

        print(f"Detected Language: {source_language}")  # Log the detected language

        # Translate to English if the source language is not English
        if source_language != target_language:
            translated_input = translate_text(user_input, src_language=source_language, dest_language=target_language)
            print(f"Translated Input (to English): {translated_input}")  # Log the translated input
        else:
            translated_input = user_input
        print(f"Translated Input (to English): {translated_input}")  # Log the translated input

        llm = OpenAI(temperature=0.5)
        with sqlite3.connect('personal_assistant.db') as conn:
            cursor = conn.cursor()
            txt_qa_pairs = load_txt_data(txt_filepath)

            # Check for an answer in the text data
            txt_response = get_answer(cursor, translated_input, txt_qa_pairs)
            if txt_response:
                # Translate back to the original language if needed
                translated_response = translate_text(txt_response, dest_language=source_language) if source_language != target_language else txt_response
                print(f"Response from TXT: {translated_response}")  # Log the response from TXT data
                return translated_response

            # Check for an answer in the database
            db_response = get_from_db(cursor, translated_input)
            if db_response:
                translated_response = translate_text(db_response, dest_language=source_language) if source_language != target_language else db_response
                print(f"Response from DB: {translated_response}")  # Log the response from the database
                return translated_response

            # If not found, use the LLM
            response = llm(translated_input)
            store_in_db(conn, cursor, translated_input, response)
            translated_response = translate_text(response, dest_language=source_language) if source_language != target_language else response
            print(f"Response from LLM: {translated_response}")  # Log the response from LLM
            return translated_response

    except Exception as e:
        print(f"Error in generate_response: {e}")
        return str(e)



    except Exception as e:
        print(f"Error in generate_response: {e}")
        return str(e)






if __name__ == "__main__":
    chat_with_assistant('data.txt')