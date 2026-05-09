import os
from dotenv import load_dotenv
#-------------------------------------------------
load_dotenv()
#-------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("GROQ_MODEL_NAME")
MAX_HISTORY = int(os.getenv("MAX_HISTORY", 10))

if not MODEL_NAME:
    raise ValueError("GROQ_MODEL_NAME is not set")
    