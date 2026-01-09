from pydantic import BaseModel, Field, HttpUrl, field_validator
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
