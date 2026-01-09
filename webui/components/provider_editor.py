import streamlit as st
from core.config_io import load_config, save_config
from utils.parsing import parse_csv_list


def provider_editor():
    st.header("Providers")
    st.caption("Manage upstream providers used by the gateway.")

    cfg = load_config()
    providers = cfg["providers"]

    left, right = st.columns([1, 2], gap="large")

    with left:
        st.subheader("Provider list")
        if not providers:
            st.info("No providers yet. Create one to start routing traffic.")
        selected = st.selectbox(
            "Select provider",
            ["<new>"] + sorted(providers.keys()),
        )

    with right:
        with st.form("provider_form"):
            if selected == "<new>":
                name = st.text_input(
                    "Provider name",
                    placeholder="openai",
                )
                base_url = st.text_input(
                    "Base URL",
                    placeholder="https://api.example.com/v1",
                )
                env_key = st.text_input(
                    "API key",
                    placeholder="OPENAI_API_KEY",
                    help="API key.",
                )
                models = st.text_area(
                    "Allowed models",
                    "*",
                    help="Comma-separated list or '*' for all.",
                )
            else:
                p = providers[selected]
                name = st.text_input(
                    "Provider name",
                    selected,
                    disabled=True,
                )
                base_url = st.text_input("Base URL", p["base_url"])
                env_key = st.text_input(
                    "API key",
                    p["api_key"],
                    help="API key.",
                )
                models = st.text_area(
                    "Allowed models",
                    ",".join(p["allowed_models"]),
                    help="Comma-separated list or '*' for all.",
                )

            save = st.form_submit_button("💾 Save provider")
            delete = st.form_submit_button("🗑 Delete provider")

        confirm_delete = False
        if selected != "<new>":
            confirm_delete = st.checkbox(
                "Confirm delete",
                help="This will remove the provider from config.yaml.",
            )

        if save:
            errors = []
            name = name.strip()
            base_url = base_url.strip()
            env_key = env_key.strip()
            allowed_models = parse_csv_list(models) or ["*"]

            if not name:
                errors.append("Provider name is required.")
            if selected == "<new>" and name in providers:
                errors.append("Provider name already exists.")
            if not base_url:
                errors.append("Base URL is required.")
            elif not (
                base_url.startswith("http://") or base_url.startswith("https://")
            ):
                errors.append("Base URL must start with http:// or https://.")
            if not env_key:
                errors.append("Env API key name is required.")

            if errors:
                for err in errors:
                    st.error(err)
            else:
                providers[name] = {
                    "base_url": base_url,
                    "api_key": env_key,
                    "allowed_models": allowed_models,
                }
                save_config(cfg)
                st.success("Provider saved")

        if delete and selected != "<new>":
            if not confirm_delete:
                st.error("Confirm deletion to proceed.")
                return
            del providers[selected]
            save_config(cfg)
            st.success("Provider deleted")
            st.rerun()
