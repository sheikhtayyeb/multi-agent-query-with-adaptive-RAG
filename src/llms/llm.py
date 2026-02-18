from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

class LLM:
    def __init__(self,model_openai = "gpt-4o-mini",model_groq = "qwen/qwen3-32b"):
        self.llm_openai = ChatOpenAI(model=model_openai, temperature=0)
        self.llm_groq = ChatGroq(model = model_groq)
