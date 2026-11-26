import streamlit as st
from dotenv import load_dotenv
import os
from streamlit.errors import StreamlitSecretNotFoundError

load_dotenv()

AI_MODEL = "gemini-3.5-flash"
AI_BACKUP_MODEL = "gemini-3.1-flash-lite"

def get_setting(name, default=None):
    try:
        value = st.secrets.get(name)
    except StreamlitSecretNotFoundError:
        value = None
    return value if value is not None else os.getenv(name, default)


GEMINI_API_KEY = get_setting("GEMINI_API_KEY")
OPENAI_API_KEY = get_setting("OPENAI_API_KEY")
