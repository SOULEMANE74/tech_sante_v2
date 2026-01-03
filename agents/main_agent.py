from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import HumanMessage
from sources.prompts import main_prompt
from dotenv import load_dotenv
from pathlib import Path
import sys
import os
import contextvars  

# --- GESTION DU CONTEXTE (Pour passer le session_id) ---
current_session_id = contextvars.ContextVar("session_id", default="default_thread")

# Importez les créateurs d'agents
from agents.emergency_agent import emergency_agent
from agents.pharmacy_agent import pharmacy_agent

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
load_dotenv()

print("[INFO] Initialisation des sous-agents...")
EMERGENCY_BOT = emergency_agent()
PHARMACY_BOT = pharmacy_agent()

# --- DÉFINITION DES OUTILS CORRIGÉE ---

@tool
def cal_emergency_agent(q: str):
    """Appel de l'agent d'orientation d'urgence pour analyser les symptômes."""
    # Récupération dynamique de l'ID de session
    user_session = current_session_id.get()
    
    # On crée un thread unique pour ce sous-agent : session_user + "_emergency"
    sub_config = {"configurable": {"thread_id": f"{user_session}_emergency"}}
    
    response = EMERGENCY_BOT.invoke(
        {"messages": [HumanMessage(content=q)]}, 
        config=sub_config
    )
    return response["messages"][-1].content

@tool
def cal_pharmacy_agent(q: str):
    """Appel de l'agent pharmacie."""
    user_session = current_session_id.get()
    sub_config = {"configurable": {"thread_id": f"{user_session}_pharma"}}
    
    response = PHARMACY_BOT.invoke(
        {"messages": [HumanMessage(content=q)]}, 
        config=sub_config
    )
    return response["messages"][-1].content

# --- ORCHESTRATEUR ---
def orchestrator_agent():
    api_key = os.environ.get('GROQ_API_KEY')
    llm = ChatGroq(model="openai/gpt-oss-120b", api_key=api_key, temperature=0)
    
    agent = create_agent(
        model=llm,
        tools=[cal_emergency_agent, cal_pharmacy_agent],
        checkpointer=InMemorySaver(),
        system_prompt=main_prompt,
    )
    return agent
