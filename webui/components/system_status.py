import streamlit as st
from core.gateway_api import get_status
from core.paths import CONFIG_PATH


def system_status():
    st.header("System")
    st.caption("Gateway status and configuration.")

    st.button("Refresh status")

    try:
        resp = get_status()
    except Exception as exc:
        st.error(f"Failed to reach gateway: {exc}")
        resp = None

    if resp is not None:
        if resp.ok:
            st.subheader("Gateway status")
            st.json(resp.json())
        else:
            st.error(resp.text)

    st.subheader("Configuration")
    if CONFIG_PATH.exists():
        with st.expander("View raw config.yaml", expanded=False):
            st.code(CONFIG_PATH.read_text(), language="yaml")
    else:
        st.warning("config.yaml not found.")
