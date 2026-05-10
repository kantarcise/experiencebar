from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from math import floor
from typing import Any

DIFFICULTY_XP: dict[str, int] = {
    "trivial": 10,
    "easy": 25,
    "medium": 60,
    "hard": 120,
    "epic": 250,
}


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def xp_required_for_level(level: int) -> int:
    if level < 1:
        raise ValueError("level must be at least 1")
    previous = level - 1
    return 100 + previous * 50 + floor(previous**1.6 * 20)


@dataclass(slots=True)
class Task:
    id: int
    title: str
    difficulty: str
    xp: int
    created_at: str
    completed_at: str | None = None

    @property
    def is_complete(self) -> bool:
        return self.completed_at is not None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        return cls(
            id=int(data["id"]),
            title=str(data["title"]),
            difficulty=str(data["difficulty"]),
            xp=int(data["xp"]),
            created_at=str(data["created_at"]),
            completed_at=data.get("completed_at"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "difficulty": self.difficulty,
            "xp": self.xp,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


@dataclass(slots=True)
class State:
    level: int = 1
    current_xp: int = 0
    lifetime_xp: int = 0
    next_task_id: int = 1
    tasks: list[Task] = field(default_factory=list)
    updated_at: str = field(default_factory=utc_now_iso)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> State:
        return cls(
            level=int(data.get("level", 1)),
            current_xp=int(data.get("current_xp", 0)),
            lifetime_xp=int(data.get("lifetime_xp", 0)),
            next_task_id=int(data.get("next_task_id", 1)),
            tasks=[Task.from_dict(item) for item in data.get("tasks", [])],
            updated_at=str(data.get("updated_at", utc_now_iso())),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "current_xp": self.current_xp,
            "lifetime_xp": self.lifetime_xp,
            "next_task_id": self.next_task_id,
            "tasks": [task.to_dict() for task in self.tasks],
            "updated_at": self.updated_at,
        }

    @property
    def xp_needed(self) -> int:
        return xp_required_for_level(self.level)

    @property
    def progress_ratio(self) -> float:
        return min(1.0, self.current_xp / self.xp_needed)

    def gain_xp(self, amount: int) -> list[int]:
        if amount < 0:
            raise ValueError("amount must be non-negative")

        self.current_xp += amount
        self.lifetime_xp += amount
        levels_gained: list[int] = []

        while self.current_xp >= self.xp_needed:
            self.current_xp -= self.xp_needed
            self.level += 1
            levels_gained.append(self.level)

        self.updated_at = utc_now_iso()
        return levels_gained

    def add_task(self, title: str, difficulty: str) -> Task:
        if difficulty not in DIFFICULTY_XP:
            choices = ", ".join(DIFFICULTY_XP)
            raise ValueError(f"difficulty must be one of: {choices}")
        if not title.strip():
            raise ValueError("title is required")

        task = Task(
            id=self.next_task_id,
            title=title.strip(),
            difficulty=difficulty,
            xp=DIFFICULTY_XP[difficulty],
            created_at=utc_now_iso(),
        )
        self.tasks.append(task)
        self.next_task_id += 1
        self.updated_at = utc_now_iso()
        return task

    def complete_task(self, task_id: int) -> tuple[Task, list[int]]:
        for task in self.tasks:
            if task.id == task_id:
                if task.is_complete:
                    raise ValueError(f"task {task_id} is already complete")
                task.completed_at = utc_now_iso()
                levels = self.gain_xp(task.xp)
                self.updated_at = utc_now_iso()
                return task, levels
        raise ValueError(f"task {task_id} was not found")
