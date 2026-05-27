import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.base_retriever import PolicyRetriever
from policies.eap.config import COLLECTION, SYSTEM_PROMPT, POLICY_NAME, TOP_K, SEM_WEIGHT
_HERE           = os.path.dirname(os.path.abspath(__file__))
VECTORSTORE_DIR = os.path.join(_HERE, '..', '..', 'vectorstore')
_retriever = PolicyRetriever(
    collection=COLLECTION, system_prompt=SYSTEM_PROMPT, policy_name=POLICY_NAME,
    top_k=TOP_K, sem_weight=SEM_WEIGHT, vectorstore_dir=VECTORSTORE_DIR,
)
def answer(query: str, chat_history: list = None) -> dict:
    return _retriever.answer(query, chat_history)
