from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from experiencebar.model import State


def default_state_file() -> Path:
    state_home = os.environ.get("XDG_STATE_HOME")
    if state_home:
        return Path(state_home) / "experiencebar" / "state.json"
    return Path.home() / ".local" / "state" / "experiencebar" / "state.json"


def load_state(path: Path) -> State:
    if not path.exists():
        return State()

    with path.open("r", encoding="utf-8") as file:
        data: dict[str, Any] = json.load(file)
    return State.from_dict(data)


def save_state(path: Path, state: State) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as file:
        json.dump(state.to_dict(), file, indent=2, sort_keys=True)
        file.write("\n")
    temporary.replace(path)
