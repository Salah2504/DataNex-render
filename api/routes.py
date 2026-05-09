from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from models.schemas import Question
from core.security import detect_injection
from ai.ai_engine import ask_ai, sessions, system_prompt
from utils.sql_utils import clean_sql, fix_informix_sql
import os

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


##------------------------------------------------
#router = APIRouter()
#
limiter = Limiter(key_func=get_remote_address)
##------------------------------------------------
#
##BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
##templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
##print("TEMPLATE PATH:", os.path.join(BASE_DIR, "templates"))
##----------------------------------------------------
#templates = Jinja2Templates(directory="templates")
#
#@router.get("/", response_class=HTMLResponse)
#def home(request: Request):
#    return templates.TemplateResponse("index.html", {"request": request})
#
## -------- ASK --------
@router.post("/ask")
@limiter.limit("5/minute")
def ask(request: Request, q: Question):

    prompt = q.question.strip()

    if not prompt:
        raise HTTPException(status_code=400, detail="Empty prompt")

    if "total" in prompt.lower():
        prompt = f"Calculate total using SUM(): {prompt}"
    elif "average" in prompt.lower():
        prompt = f"Calculate average using AVG(): {prompt}"
    elif "count" in prompt.lower():
        prompt = f"Count rows using COUNT(): {prompt}"
    response = ask_ai(prompt, q.session_id)

    

 
#    if detect_injection(prompt):
#        raise HTTPException(status_code=400, detail="⚠️ Suspicious request")
#
    # تحسين الفهم
   

 

    try:
        response = ask_ai(prompt, q.session_id)
        response = fix_informix_sql(response)
        response = clean_sql(response)
        return {
        "response": response
        }

    except Exception as e:
        import logging
        logging.error(str(e))
        raise HTTPException(status_code=500, detail="AI failed")

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