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

# Importez les créateurs d'agents, mais on ne va pas les appeler dans l'outil
from agents.emergency_agent import emergency_agent
from agents.pharmacy_agent import pharmacy_agent

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
load_dotenv()

# --- 1. INITIALISATION GLOBALE (Singleton) ---
# On crée les instances des sous-agents UNE SEULE FOIS ici.
print("[INFO] Initialisation des sous-agents...")
EMERGENCY_BOT = emergency_agent()
PHARMACY_BOT = pharmacy_agent()

# --- 2. DÉFINITION DES OUTILS ---

@tool
def cal_emergency_agent(q: str):
    """Appel de l'agent d'orientation d'urgence pour analyser les symptômes."""
    # On utilise une config jetable ou on génère un ID unique pour cet appel interne
    # Pour l'instant, un ID statique suffit car l'agent est stateless entre les appels du main
    sub_config = {"configurable": {"thread_id": "sub_emergency_1"}}
    
    # On appelle l'instance déjà créée
    response = EMERGENCY_BOT.invoke(
        {"messages": [HumanMessage(content=q)]}, 
        config=sub_config
    )
    return response["messages"][-1].content

@tool
def cal_pharmacy_agent(q: str):
    """Appel de l'agent pharmacie pour trouver des médicaments ou gardes."""
    sub_config = {"configurable": {"thread_id": "sub_pharma_1"}}
    
    response = PHARMACY_BOT.invoke(
        {"messages": [HumanMessage(content=q)]}, 
        config=sub_config
    )
    return response["messages"][-1].content

# --- 3. ORCHESTRATEUR ---

def orchestrator_agent():
    api_key = os.environ.get('GROQ_API_KEY')
    llm = ChatGroq(
        model="openai/gpt-oss-120b", 
        api_key=api_key, 
        temperature=0,
    )

    agent = create_agent(
        model = llm,
        tools = [cal_emergency_agent, cal_pharmacy_agent],
        checkpointer = InMemorySaver(),
        system_prompt = main_prompt,
    )

    return agent
