import os
from langchain_groq import ChatGroq

def get_chatgroq_model():
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="llama-3.1-8b-instant"
    )
