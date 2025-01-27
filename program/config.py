from groq import Groq
import streamlit as st

# Configuración inicial
client = Groq()

# Groq Models
groq_models = {
    "llama-3.3-70b-versatile":{
        "name": "LLaMA-3.3-70b-Versatile",
        "tokens": 32768,
        "developer": "Meta",
    },
    "llama3-70b-8192": {
        "name": "LLaMA3-70b-Instruct",
        "tokens": 8192,
        "developer": "Meta",
    },
    "llama3-8b-8192": {
        "name": "LLaMA3-8b-Instruct",
        "tokens": 8192,
        "developer": "Meta",
    },
    "mixtral-8x7b-32768": {
        "name": "Mixtral-8x7b-Instruct-v0.1",
        "tokens": 32768,
        "developer": "Mistral",
    },
    "gemma2-9b-it": {"name": "Gemma2-9b-it", "tokens": 8192, "developer": "Google"},
}