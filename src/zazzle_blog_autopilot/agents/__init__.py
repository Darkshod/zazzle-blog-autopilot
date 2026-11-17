"""Base agent contract and structured TaskResult logging."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..config import AppSettings
from ..db import Database
from ..models import TaskResult


class BaseAgent(ABC):
    name: str = "base_agent"

    def __init__(self, db: Database, settings: AppSettings) -> None:
        self.db = db
        self.settings = settings

    @abstractmethod
    def execute(self, **kwargs: Any) -> TaskResult:
        """Run the agent's task and return a structured TaskResult."""

    def run(self, **kwargs: Any) -> TaskResult:
        try:
            result = self.execute(**kwargs)
        except Exception as exc:  # pragma: no cover - defensive logging
            result = TaskResult(
                agent_name=self.name,
                task=kwargs.get("task", self.name),
                status="error",
                input_summary={k: str(v)[:120] for k, v in kwargs.items()},
                errors=[str(exc)],
                recommendations=["Inspect agent inputs and retry job."],
            )
        self.db.log_agent_result(result)
        return result
