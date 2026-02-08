import uvicorn
from fastapi import FastAPI, HTTPException, Form, Response, UploadFile, File, requests
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from sources.stt_transcribe import transcribe_audio
import uuid
import shutil

import sys
import os

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from agents.main_agent import current_session_id
from agents.main_agent import orchestrator_agent 
from langchain.messages import HumanMessage

app = FastAPI(
    title="TechSanté API",
    description="API de régulation médicale pour le Grand Lomé",
    version="1.0"
)

# --- Modèles de données (Pydantic) ---
class UserRequest(BaseModel):
    query: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    session_id: Optional[str] = None

class AgentResponse(BaseModel):
    response: str
    session_id: str

# --- Initialisation de l'agent ---

orchestrator = orchestrator_agent()

@app.get("/")
def read_root():
    return {"status": "TechSanté API is running"}

@app.post("/triage", response_model=AgentResponse)
async def triage_endpoint(request: UserRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        # On définit le contexte pour cette requête ---
        token = current_session_id.set(session_id) 
        
        config = {"configurable": {"thread_id": session_id}}

        context_msg = request.query
        if request.latitude and request.longitude:
            context_msg += f"\n[SYSTEM DATA: User Location is LAT:{request.latitude}, LON:{request.longitude}]"

        result = orchestrator.invoke(
            {"messages": [HumanMessage(content=context_msg)]}, 
            config=config
        )

        bot_response = result['messages'][-1].content

        current_session_id.reset(token)

        return AgentResponse(
            response=bot_response,
            session_id=session_id
        )
        
    except Exception as e:
    
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur interne du système de triage.")
    
@app.post("/triage-vocal")
async def triage_vocal(file: UploadFile = File(...), session_id: Optional[str] = None):
    temp_path = f"temp_{uuid.uuid4()}_{file.filename}" 
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Transcription
        text_query = transcribe_audio(temp_path)
        
        sid = session_id or str(uuid.uuid4())
        token = current_session_id.set(sid)
        config = {"configurable": {"thread_id": sid}}

        # Appel de l'orchestrateur 
        result = orchestrator.invoke(
            {"messages": [HumanMessage(content=text_query)]}, 
            config=config
        )

        bot_response = result['messages'][-1].content
        current_session_id.reset(token)

        return {
            "status": "success",
            "session_id": sid,
            "transcription": text_query,
            "ai_response": bot_response
        }

    except Exception as e:
        print(f"Error Vocal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur STT/Agent: {str(e)}")
    
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)