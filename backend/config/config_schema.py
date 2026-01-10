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
                if "*" in key.models or "*" in provider_models:
                    continue

                # model compatibility
                for model in key.models:
                    if model not in provider_models:
                        errors.append(
                            f"gateway_keys.{key_name}: model '{model}' "
                            f"not allowed by provider '{provider}'"
                        )
                        
        if errors:
            raise ValueError("Invalid gateway configuration:\n" + "\n".join(errors))

        return self
