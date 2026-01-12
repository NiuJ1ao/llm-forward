from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator
from typing import Dict, List, Optional
from datetime import datetime


class ProviderConfigModel(BaseModel):
    base_url: HttpUrl
    api_key: str
    allowed_models: List[str] = Field(min_length=1)

    @field_validator("base_url", mode="before")
    @classmethod
    def strip_trailing_slash(cls, v: str):
        return v.rstrip("/")


class GatewayKeyModel(BaseModel):
    owner: str
    providers: List[str] = Field(min_length=1)
    models: List[str] = Field(min_length=1)
    expires_at: Optional[datetime] = None

    @field_validator("expires_at")
    @classmethod
    def must_be_utc(cls, v):
        if v and v.tzinfo is None:
            raise ValueError("expires_at must be timezone-aware (UTC)")
        return v


class GatewayConfigModel(BaseModel):
    providers: Dict[str, ProviderConfigModel]
    gateway_keys: Dict[str, GatewayKeyModel]

    @model_validator(mode="after")
    def validate_references(self):
        errors: list[str] = []

        # ---- validate gateway keys ----
        for key_name, key in self.gateway_keys.items():
            # Allow models if they are valid for at least one listed provider.
            key_allows_all_models = "*" in key.models
            model_allowed_by_any_provider = {m: False for m in key.models}
            # provider existence
            for provider in key.providers:
                if provider not in self.providers:
                    errors.append(
                        f"gateway_keys.{key_name}: unknown provider '{provider}'"
                    )
                    continue

                provider_cfg = self.providers[provider]
                provider_models = provider_cfg.allowed_models

                # wildcard short-circuit
                if key_allows_all_models or "*" in provider_models:
                    continue

                # model compatibility: mark models allowed by any provider
                for model in key.models:
                    if model in provider_models:
                        model_allowed_by_any_provider[model] = True

            # after checking providers, fail only models unsupported by all providers
            if not key_allows_all_models:
                for model, allowed in model_allowed_by_any_provider.items():
                    if not allowed:
                        errors.append(
                            f"gateway_keys.{key_name}: model '{model}' "
                            f"not allowed by any configured provider"
                        )

        if errors:
            raise ValueError("Invalid gateway configuration:\n" + "\n".join(errors))

        return self
