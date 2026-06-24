from fastapi import APIRouter, HTTPException, Request
#from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
#from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from models.schemas import Question
from core.security import detect_injection
from ai.ai_engine import ask_ai, sessions#, system_prompt
from utils.sql_utils import clean_sql, fix_informix_sql
#import os
##------------------------------------------------

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
templates = Jinja2Templates(directory="templates")

##------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

#limiter = Limiter(key_func=get_remote_address)

## -------- ASK --------
@router.post("/ask")
@limiter.limit("5/minute")
def ask(request: Request, q: Question):

    prompt = q.question.strip()

    if not prompt:
        raise HTTPException(status_code=400, detail="Empty prompt")

    # حماية ضد prompt injection
    if detect_injection(prompt):
        raise HTTPException(
            status_code=400,
            detail="Potential prompt injection detected"
        )

    if "total" in prompt.lower():
        prompt = f"Calculate total using SUM(): {prompt}"

    elif "average" in prompt.lower():
        prompt = f"Calculate average using AVG(): {prompt}"

    elif "count" in prompt.lower():
        prompt = f"Count rows using COUNT(): {prompt}"

    try:
        response = ask_ai(prompt, q.session_id)
        response = fix_informix_sql(response)
        response = clean_sql(response)
        response = response.split("```sql")[-1]
        response = response.split("```")[0]
        if "This query" in response or "will return" in response:
            response = response.split("SELECT")[-1]
            response = "SELECT" + response
#        if not response.strip().endswith(")"):
#            response += "\n-- WARNING: possible truncated SQL"
        return {
            "response": response
        }
    except Exception as e:
        import logging
        logging.error(str(e))
    
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# -------- STREAM --------
@router.post("/ask-stream")
@limiter.limit("5/minute")
def ask_stream(q: Question, request: Request):

    def generate():
        try:
            if q.session_id not in sessions:
                sessions[q.session_id] = []

            chat_history = sessions[q.session_id]

            chat_history.append({"role": "user", "content": q.question})

            messages = [system_prompt] + chat_history

            stream = ask_ai(q.question, q.session_id)

            yield stream

        except Exception as e:
            yield f"[ERROR]: {str(e)}"

    return StreamingResponse(generate(), media_type="text/plain")

# -------- CLEAR --------
@router.post("/clear")
def clear(q: Question):
    sessions[q.session_id] = [system_prompt]
    return {"status": "cleared"}  