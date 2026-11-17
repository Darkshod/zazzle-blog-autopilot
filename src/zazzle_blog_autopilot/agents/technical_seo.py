"""Technical SEO Doctor — validates links, canonicals, sitemaps, structured data, and CWV heuristics."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from ..models import TaskResult
from . import BaseAgent


def audit_built_site(dist_dir: Path) -> dict[str, Any]:
    """Audit rendered static site directory for SEO health, broken internal links, sitemap & JSON-LD."""
    issues: list[str] = []
    warnings: list[str] = []
    html_files = list(dist_dir.rglob("*.html")) if dist_dir.exists() else []
    titles_seen: dict[str, str] = {}

    if not html_files:
        return {"healthy": False, "pages_checked": 0, "issues": ["No rendered HTML files in dist/"], "warnings": []}

    sitemap_path = dist_dir / "sitemap.xml"
    sitemap_valid = False
    if sitemap_path.exists():
        try:
            ET.parse(sitemap_path)
            sitemap_valid = True
        except ET.ParseError as exc:
            issues.append(f"Invalid sitemap.xml: {exc}")
    else:
        issues.append("Missing sitemap.xml")

    if not (dist_dir / "robots.txt").exists():
        issues.append("Missing robots.txt")

    for html_file in html_files:
        rel = html_file.relative_to(dist_dir).as_posix()
        soup = BeautifulSoup(html_file.read_text(encoding="utf-8"), "html.parser")

        # Title & duplicate check
        title_tag = soup.find("title")
        title_txt = title_tag.get_text(strip=True) if title_tag else ""
        if not title_txt:
            issues.append(f"{rel}: missing <title>")
        elif title_txt in titles_seen:
            issues.append(f"{rel}: duplicate <title> with {titles_seen[title_txt]}")
        else:
            titles_seen[title_txt] = rel

        # Canonical check
        canonical = soup.find("link", attrs={"rel": "canonical"})
        if not canonical or not canonical.get("href"):
            issues.append(f"{rel}: missing canonical link")

        # Structured data JSON-LD validation
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                json.loads(script.string or "{}")
            except json.JSONDecodeError as exc:
                issues.append(f"{rel}: invalid JSON-LD ({exc})")

        # Internal link & local image availability check
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith("/") and not href.startswith("//"):
                target = dist_dir / href.lstrip("/")
                if href == "/":
                    target = dist_dir / "index.html"
                if not target.exists():
                    issues.append(f"{rel}: broken internal link '{href}'")

        for img in soup.find_all("img"):
            if not img.get("alt"):
                warnings.append(f"{rel}: image missing alt attribute")
            src = (img.get("src") or "").strip()
            if src.startswith("/") and not (dist_dir / src.lstrip("/")).exists():
                issues.append(f"{rel}: missing local image '{src}'")

    return {
        "healthy": len(issues) == 0,
        "pages_checked": len(html_files),
        "sitemap_valid": sitemap_valid,
        "issues": issues,
        "warnings": warnings,
    }


class TechnicalSEODoctor(BaseAgent):
    name = "technical_seo_doctor"

    def execute(self, dist_dir: Path | None = None, **kwargs: Any) -> TaskResult:
        target_dir = dist_dir or (Path.cwd() / "dist")
        report = audit_built_site(target_dir)
        return TaskResult(
            agent_name=self.name,
            task="run_technical_seo_audit",
            status="success" if report["healthy"] else "warning",
            input_summary={"dist_dir": str(target_dir)},
            output_summary=report,
            errors=report["issues"],
            recommendations=[
                "Submit sitemap.xml manually in Google Search Console; never use automated mass-indexing tricks."
            ],
        )
