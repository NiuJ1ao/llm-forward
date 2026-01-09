import streamlit as st

# from datetime import datetime, timezone
# from core.gateway_api import reload_gateway
from core.paths import CONFIG_PATH, GATEWAY_BASE


def sidebar_navigation():
    st.sidebar.title("LLM Gateway")
    st.sidebar.caption("Admin console")

    page = st.sidebar.radio(
        "Navigation",
        ["Providers", "API Keys", "Usage", "System"],
        label_visibility="collapsed",
    )

    st.sidebar.divider()

    st.sidebar.caption(f"Gateway: {GATEWAY_BASE}")
    st.sidebar.caption(f"Config: {CONFIG_PATH}")
    # confirm_reload = st.sidebar.checkbox(
    #     "Confirm apply",
    #     help="Prevents accidental reloads while editing.",
    # )

    # if st.sidebar.button(
    #     "Apply config to gateway",
    #     # disabled=not confirm_reload,
    #     use_container_width=True,
    # ):
    #     with st.spinner("Reloading gateway..."):
    #         try:
    #             resp = reload_gateway()
    #         except Exception as exc:
    #             st.sidebar.error(f"Reload failed: {exc}")
    #         else:
    #             if resp.ok:
    #                 ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    #                 st.sidebar.success(f"Gateway reloaded at {ts}")
    #             else:
    #                 st.sidebar.error(resp.text)

    return page
