from groq import Groq
from core.config import GROQ_API_KEY, MODEL_NAME, MAX_HISTORY
import logging
from core.logger import logger
#------------------------------------------------------------
client = Groq(api_key=GROQ_API_KEY)

sessions = {}

system_prompt = {
    "role": "system",
    "content": """
You are DataNex AI, an expert IBM Informix SQL assistant.

STRICT RULES:
- Only generate SELECT queries
- Never modify data

SMART RULES:
- total → SUM()
- count → COUNT()
- average → AVG()

Return SQL inside ```sql``` block only.
"""
}

#--------------------------------------------------------------
def ask_ai(prompt, session_id):

    #logging.info(f"User prompt: {prompt}") 
    logger.info(f"User Prompt: {prompt}")    

    if session_id not in sessions:
        sessions[session_id] = []

    chat_history = sessions[session_id]

    chat_history.append({
        "role": "user",
        "content": prompt
    })

    messages = [system_prompt] + chat_history[-MAX_HISTORY:]

    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages
    )

    reply = completion.choices[0].message.content

    #logging.info(f"AI response: {reply}") 
    logger.info(f"AI Response: {reply}")

    chat_history.append({
        "role": "assistant",
        "content": reply
    })
    try:
        return reply
    except Exception as e:
        logger.error(str(e))