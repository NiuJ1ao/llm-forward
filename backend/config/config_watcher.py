import asyncio
from pathlib import Path

from backend.config.config_store import ConfigStore

CONFIG_PATH = Path("config.yaml")
POLL_INTERVAL = 1.0  # seconds


async def watch_config_file():
    last_mtime = None

    while True:
        try:
            mtime = CONFIG_PATH.stat().st_mtime

            if last_mtime is None:
                last_mtime = mtime

            elif mtime != last_mtime:
                ok = ConfigStore.load()

                if ok:
                    print("[config] Reloaded successfully")
                else:
                    print(
                        "[config] Reload failed, rolled back:",
                        ConfigStore.status()["last_error"],
                    )

                last_mtime = mtime

        except FileNotFoundError:
            print("[config] config.yaml not found (ignored)")

        except Exception as e:
            # Never crash the watcher
            print("[config] Watcher error:", e)

        await asyncio.sleep(POLL_INTERVAL)
