import yaml
from .paths import CONFIG_PATH


def load_config():
    cfg = yaml.safe_load(CONFIG_PATH.read_text()) or {}
    cfg.setdefault("providers", {})
    cfg.setdefault("gateway_keys", {})
    return cfg


def save_config(cfg):
    CONFIG_PATH.write_text(yaml.safe_dump(cfg, sort_keys=False))
