from datetime import datetime, timezone
import streamlit as st

from core.config_io import load_config, save_config


def key_editor():
    st.header("API Keys")
    st.caption("Manage gateway keys and access policies.")

    cfg = load_config()
    keys = cfg["gateway_keys"]
    providers = sorted(cfg["providers"].keys())

    left, right = st.columns([1, 2], gap="large")

    with left:
        st.subheader("Key list")
        if not keys:
            st.info("No keys yet. Create one to allow access.")
        selected = st.selectbox(
            "Select API key",
            ["<new>"] + sorted(keys.keys()),
        )

    local_tz = datetime.now().astimezone().tzinfo

    if selected != "<new>":
        raw_expires = keys[selected].get("expires_at")
        try:
            default_expires = (
                datetime.fromisoformat(raw_expires.replace("Z", "+00:00"))
                if raw_expires
                else None
            )
        except Exception:
            default_expires = None
    else:
        default_expires = None

    with right:
        if not providers:
            st.warning("Create providers first to assign access.")
        st.subheader("Expires at (optional)")

        expiry_key = f"expiry_enabled_{selected}"
        date_key = f"expiry_date_{selected}"
        time_key = f"expiry_time_{selected}"

        enable_expiry = st.checkbox(
            "Enable expiration (local time)",
            value=default_expires is not None,
            key=expiry_key,
        )

        expires_at = None

        col1, col2 = st.columns(2)

        with col1:
            expiry_date = st.date_input(
                "Expiration date (local)",
                value=(
                    default_expires.astimezone(local_tz).date()
                    if default_expires
                    else datetime.now().astimezone().date()
                ),
                key=date_key,
                disabled=not enable_expiry,
            )

        with col2:
            expiry_time = st.time_input(
                "Expiration time (local)",
                value=(
                    default_expires.astimezone(local_tz).time()
                    if default_expires
                    else datetime.now().astimezone().time().replace(microsecond=0)
                ),
                key=time_key,
                disabled=not enable_expiry,
            )

        if enable_expiry:
            local_dt = datetime.combine(
                expiry_date,
                expiry_time,
                tzinfo=local_tz,
            )
            expires_at = local_dt.astimezone(timezone.utc)
            st.caption(f"UTC timestamp: {expires_at.strftime('%Y-%m-%d %H:%M:%SZ')}")
        else:
            st.caption("Local time will be converted to UTC on save.")

        missing_providers = []
        missing_providers_in_config = []
        if selected == "<new>":
            key = st.text_input(
                "Gateway key",
                placeholder="fk-...",
                key=f"gateway_key_{selected}",
            )
            owner = st.text_input(
                "Owner",
                placeholder="alice",
                key=f"owner_{selected}",
            )
            allowed_providers = st.multiselect(
                "Providers",
                providers,
                help="Select at least one provider.",
                key=f"providers_{selected}",
            )
            existing_models = ["*"]
        else:
            k = keys[selected]
            key = selected
            st.text_input(
                "Gateway key",
                selected,
                disabled=True,
                key=f"gateway_key_{selected}",
            )
            owner = st.text_input(
                "Owner",
                k["owner"],
                key=f"owner_{selected}",
            )
            allowed_providers = st.multiselect(
                "Providers",
                providers,
                default=[p for p in k["providers"] if p in providers],
                help="Select at least one provider.",
                key=f"providers_{selected}",
            )
            missing_providers_in_config = [
                p for p in k["providers"] if p not in providers
            ]
            if missing_providers_in_config:
                st.warning(
                    "Some providers referenced by this key no longer exist: "
                    + ", ".join(missing_providers_in_config)
                )
            existing_models = k["models"]

        missing_providers = [p for p in allowed_providers if p not in providers]

        selected_provider_models = []
        wildcard_available = False
        for provider in allowed_providers:
            provider_cfg = cfg["providers"].get(provider, {})
            provider_models = provider_cfg.get("allowed_models", [])
            if "*" in provider_models:
                wildcard_available = True
            selected_provider_models.extend(
                [model for model in provider_models if model != "*"]
            )

        valid_model_options = sorted(set(selected_provider_models))
        if wildcard_available:
            valid_model_options = ["*"] + valid_model_options

        extra_models = [
            model
            for model in existing_models
            if model not in valid_model_options and model != "*"
        ]
        model_options = valid_model_options + extra_models

        if "*" in existing_models and wildcard_available:
            default_models = ["*"]
        elif model_options:
            default_models = [m for m in existing_models if m in model_options]
        else:
            default_models = []

        if not model_options:
            st.info("Select providers to see available models.")

        models_key = f"models_{selected}"
        if models_key not in st.session_state:
            st.session_state[models_key] = default_models
        current_models = st.session_state[models_key]
        if current_models:
            if "*" in current_models and not wildcard_available:
                current_models = [m for m in current_models if m != "*"]
            current_models = [m for m in current_models if m in valid_model_options]
            st.session_state[models_key] = current_models

        selected_models = st.multiselect(
            "Models",
            model_options,
            help="Models are limited to the selected providers.",
            disabled=not model_options,
            key=models_key,
        )
        missing_models = [
            model
            for model in selected_models
            if model not in valid_model_options and model != "*"
        ]
        if "*" in selected_models and not wildcard_available:
            missing_models.append("*")
        if missing_models:
            st.warning(
                "Some models referenced by this key are not allowed by the "
                "selected providers: " + ", ".join(sorted(set(missing_models)))
            )
        has_missing_refs = bool(missing_providers or missing_models)

        col_save, col_delete = st.columns(2)
        with col_save:
            save = st.button(
                "💾 Save key",
                use_container_width=True,
                disabled=has_missing_refs,
            )
        with col_delete:
            delete = st.button("🗑 Delete key", use_container_width=True)

        confirm_delete = False
        if selected != "<new>":
            confirm_delete = st.checkbox(
                "Confirm delete",
                help="This will remove the key from config.yaml.",
            )

        if save:
            errors = []
            key = key.strip()
            owner = owner.strip()
            allowed_providers = [p for p in allowed_providers if p in providers]
            effective_models = [m for m in model_options if m != "*"]
            if "*" in selected_models:
                allowed_models = ["*"] if wildcard_available else []
            else:
                allowed_models = [m for m in selected_models if m in effective_models]

            if not key:
                errors.append("Gateway key is required.")
            if selected == "<new>" and key in keys:
                errors.append("Gateway key already exists.")
            if not owner:
                errors.append("Owner is required.")
            if not providers:
                errors.append("Create at least one provider before saving a key.")
            elif not allowed_providers:
                errors.append("Select at least one provider.")
            elif not allowed_models:
                errors.append("Select at least one model.")
            if missing_providers:
                errors.append("Remove missing providers before saving.")
            if missing_models:
                errors.append("Remove missing models before saving.")

            if errors:
                for err in errors:
                    st.error(err)
            else:
                keys[key] = {
                    "owner": owner,
                    "providers": allowed_providers,
                    "models": allowed_models,
                    "expires_at": (
                        expires_at.isoformat().replace("+00:00", "Z")
                        if expires_at
                        else None
                    ),
                }
                save_config(cfg)
                st.success("Key saved")

        if delete and selected != "<new>":
            if not confirm_delete:
                st.error("Confirm deletion to proceed.")
                return
            del keys[selected]
            save_config(cfg)
            st.success("Key deleted")
            st.rerun()
