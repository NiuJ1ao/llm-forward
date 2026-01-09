import streamlit as st
from components.sidebar import sidebar_navigation
from components.provider_editor import provider_editor
from components.key_editor import key_editor
from components.usage_dashboard import usage_dashboard
from components.system_status import system_status

st.set_page_config(page_title="LLM Gateway Admin", layout="wide")
st.title("LLM Gateway Admin")
st.caption("Configure providers, keys, and usage reporting.")

page = sidebar_navigation()

if page == "Providers":
    provider_editor()
elif page == "API Keys":
    key_editor()
elif page == "Usage":
    usage_dashboard()
elif page == "System":
    system_status()
