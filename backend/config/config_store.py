import yaml
import threading
import time
from pathlib import Path
from typing import Optional

from backend.config.config_schema import GatewayConfigModel

CONFIG_PATH = Path("config.yaml")


class ConfigSnapshot:
    def __init__(self, config: GatewayConfigModel):
        self.config = config
        self.version = int(time.time())
        self.loaded_at = time.time()


class ConfigStore:
    _lock = threading.Lock()
    _current: Optional[ConfigSnapshot] = None
    _last_error: Optional[str] = None

    @classmethod
    def load(cls) -> bool:
        try:
            raw = yaml.safe_load(CONFIG_PATH.read_text())

            parsed = GatewayConfigModel.model_validate(raw)

            # for name, provider in parsed.providers.items():
            #     if provider.env_api_key not in os.environ:
            #         raise ValueError(
            #             f"Provider '{name}': env var {provider.env_api_key} not set"
            #         )

            snapshot = ConfigSnapshot(parsed)

            with cls._lock:
                cls._current = snapshot
                cls._last_error = None

            return True

        except Exception as e:
            with cls._lock:
                cls._last_error = str(e)
            return False

    @classmethod
    def get(cls) -> ConfigSnapshot:
        if cls._current is None:
            if not cls.load():
                raise RuntimeError(f"Failed to load config: {cls._last_error}")
        return cls._current

    @classmethod
    def status(cls):
        return {
            "loaded": cls._current is not None,
            "version": cls._current.version if cls._current else None,
            "loaded_at": cls._current.loaded_at if cls._current else None,
            "last_error": cls._last_error,
        }
