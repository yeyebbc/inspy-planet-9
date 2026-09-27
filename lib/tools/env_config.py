"""Resolve secret references in the local configuration file."""

import os
import re
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)

_ENV_REFERENCE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_SECRET_KEYS = {
    "sissm.RconPassword",
    "sync_data.serverKey",
    "chat.deepseekKey",
}


def resolve_secret(key: str, value: str) -> str:
    if key not in _SECRET_KEYS and not key.startswith("http_server.server["):
        return value

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in os.environ:
            raise ValueError(f"{key} 引用的环境变量 {name} 未设置")
        return os.environ[name]

    return _ENV_REFERENCE.sub(replace, value)
