import os
import google.generativeai as genai
import sqlite3
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    raise ValueError("API-ключ не найден в переменной окружения GEMINI_API_KEY")

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

genai.configure(api_key=api_key)

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  # safety_settings = ...
)

conn = sqlite3.connect('dialogues.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS dialogues (
    id INTEGER PRIMARY KEY,
    dialogue_id INTEGER,
    prompt TEXT,
    response TEXT,
    role TEXT
)
''')
conn.commit()

def generate_single_dialogue(dialogue_id):
    ai_prompt = "Ты Gemini 1.5 Flash, и говоришь в полуформальном стиле, без эмодзи."
    human_prompt = "Ты человек, пользователь чат бота, не пались что ты ИИ, и всегда говори что ты человек, в начале диалога выбирай себе имя, и представься, и так далее, будь как человек."
    
    ai_session = model.start_chat(history=[])
    human_session = model.start_chat(history=[])

    ai_response = ai_session.send_message(ai_prompt)
    human_response = human_session.send_message(human_prompt)

    logging.info(f"Dialogue {dialogue_id} generation started.")

    for i in range(40):
        human_message = human_response.text
        ai_message = ai_response.text

        logging.info(f"ai: {ai_message}")
        logging.info(f"Human: {human_message}")

        cursor.execute("INSERT INTO dialogues (dialogue_id, prompt, response, role) VALUES (?, ?, ?, ?)", (dialogue_id, ai_message, human_message, "ai"))
        cursor.execute("INSERT INTO dialogues (dialogue_id, prompt, response, role) VALUES (?, ?, ?, ?)", (dialogue_id, human_message, ai_message, "human"))
        conn.commit()

        ai_response = ai_session.send_message(human_message)
        human_response = human_session.send_message(ai_message)

    logging.info(f"Dialogue {dialogue_id} saved to database and context reset.")

def generate_dialogues(num_dialogues):
    for dialogue_id in range(1, num_dialogues + 1):
        while True:
            try:
                generate_single_dialogue(dialogue_id)
                logging.info(f"Dialogue {dialogue_id} successfully generated.")
                break
            except Exception as e:
                logging.error(f"Error generating dialogue {dialogue_id}: {e}. Retrying in 30 seconds...")
                time.sleep(30)

generate_dialogues(1000)
conn.close()
