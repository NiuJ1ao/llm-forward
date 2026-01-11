import os

import streamlit as st
from dotenv import load_dotenv
from components.sidebar import sidebar_navigation
from components.provider_editor import provider_editor
from components.key_editor import key_editor
from components.usage_dashboard import usage_dashboard
from components.system_status import system_status

load_dotenv()

st.set_page_config(page_title="LLM Gateway Admin", layout="wide")

required_password = os.getenv("WEBUI_PASSWORD")
if required_password:
    if not st.session_state.get("webui_authed"):
        st.title("LLM Gateway Admin")
        st.caption("Enter the admin password to continue.")
        password = st.text_input("Password", type="password")
        if st.button("Sign in"):
            if password == required_password:
                st.session_state["webui_authed"] = True
                st.rerun()
            else:
                st.error("Invalid password.")
        st.stop()

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
