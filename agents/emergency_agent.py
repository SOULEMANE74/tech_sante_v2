from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import HumanMessage
from sources.tools import check_beds_availability

from dotenv import load_dotenv
from pathlib import Path

import sys
import os

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
from sources.prompts import SYSTEME_PROMPTE_TEST

import  sqlite3

load_dotenv()

def emergency_agent():

    try:
        
        print("[DEBUG] : l'agent a demarrer")

        api_key = os.environ.get('GROQ_API_KEY')
        llm = ChatGroq(
            model="openai/gpt-oss-120b", 
            api_key=api_key, 
            temperature=0,
        )

        sql_agent = create_agent(
            model = llm,
            tools = [check_beds_availability],
            system_prompt = SYSTEME_PROMPTE_TEST,
            checkpointer = InMemorySaver(),

        )
        # return sql_agent

    except Exception as e:
        print(f"[BUG] l'agent n'a pas demarer !!")
        print(f"Erreur : {e}")

    return sql_agent

#     while True:
#         q = input("\nUrgence : ")
#         config = {"configurable": {"thread_id": "1"}}

#         if q.lower() == 'q': 
#             break
#         q = HumanMessage(content=q)
#         try:
#             result = sql_agent.invoke({"messages": [q]}, config=config)
#             print(result['messages'][-1].content)
#         except Exception as e:
#             print(f"[BUG] l'agent n'a pas demarer !!")
#             print(f"Erreur : {e}")

# if __name__ == '__main__':
#     emergency_agent()

