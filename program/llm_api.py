from groq import Groq
import streamlit as st
from config import client  # Import client from config

def query_llm(messages, model=None, temperature=0.5, max_tokens=1024):
    """Realiza una consulta al modelo LLM usando la API de Groq."""
    if model is None:
        model = st.session_state.selected_groq_model
    response = client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content