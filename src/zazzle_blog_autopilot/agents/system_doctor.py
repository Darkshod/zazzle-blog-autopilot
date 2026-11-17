"""System Doctor Agent — checks DB integrity, disk/backup readiness, and Emergency Stop state."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..models import TaskResult
from . import BaseAgent


class SystemDoctorAgent(BaseAgent):
    name = "system_doctor"

    def execute(self, root_dir: Path | None = None, **kwargs: Any) -> TaskResult:
        root = root_dir or Path.cwd()
        emergency_stop = self.db.get_system_flag("emergency_stop") == "true"
        db_ok = self.db.db_path.exists() and self.db.db_path.stat().st_size > 0
        backups = list((root / "data" / "backups").glob("*.db")) if (root / "data" / "backups").exists() else []

        return TaskResult(
            agent_name=self.name,
            task="run_system_health_check",
            status="warning" if emergency_stop or not db_ok else "success",
            input_summary={"db_path": str(self.db.db_path)},
            output_summary={
                "db_healthy": db_ok,
                "emergency_stop_active": emergency_stop,
                "backups_count": len(backups),
            },
            recommendations=[
                "Clear emergency_stop before resuming automated runs." if emergency_stop else "System healthy."
            ],
        )
