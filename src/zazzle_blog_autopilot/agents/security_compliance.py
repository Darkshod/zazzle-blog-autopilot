"""Security & Compliance Agent — checks secrets exposure, disclosures, and policy compliance."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..models import TaskResult
from . import BaseAgent

SECRET_PATTERNS = (
    re.compile(r"gho_[A-Za-z0-9]{20,}"),
    re.compile(r"AIza[0-9A-Za-z\-_]{20,}"),
    re.compile(r"pina_[A-Za-z0-9]{20,}"),
)


class SecurityComplianceAgent(BaseAgent):
    name = "security_compliance"

    def execute(self, root_dir: Path | None = None, **kwargs: Any) -> TaskResult:
        root = root_dir or Path.cwd()
        findings: list[str] = []

        env_file = root / ".env"
        gitignore = (root / ".gitignore").read_text(encoding="utf-8") if (root / ".gitignore").exists() else ""
        if ".env" not in gitignore:
            findings.append(".env is missing from .gitignore")

        for py_file in (root / "src").rglob("*.py") if (root / "src").exists() else []:
            txt = py_file.read_text(encoding="utf-8", errors="ignore")
            for pat in SECRET_PATTERNS:
                if pat.search(txt):
                    findings.append(f"Potential hardcoded secret in {py_file.name}")

        undisclosed = [
            a.slug for a in self.db.list_articles() if not a.affiliate_disclosure_included
        ]
        if undisclosed:
            findings.append(f"Articles missing affiliate disclosure: {undisclosed}")

        return TaskResult(
            agent_name=self.name,
            task="run_security_and_compliance_scan",
            status="success" if not findings else "warning",
            input_summary={"root_dir": str(root), "local_env_present": env_file.exists()},
            output_summary={"clean": len(findings) == 0, "findings": findings},
            errors=findings,
            recommendations=["Keep all API tokens in .env or GitHub Actions Secrets; never commit credentials."],
        )
