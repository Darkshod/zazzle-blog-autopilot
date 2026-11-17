"""Command-line interface for Zazzle Blog Autopilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import uvicorn

from .agents.manager import ManagerAgent
from .config import load_settings
from .dashboard import create_app
from .db import Database
from .site_builder import StaticBlogBuilder


def main() -> None:
    parser = argparse.ArgumentParser(description="Zazzle Blog Autopilot CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run-all", help="Run the full 12-agent pipeline")
    run_p.add_argument("--csv", type=Path, default=Path("data/sample_products.csv"))
    run_p.add_argument("--max-articles", type=int, default=4)
    run_p.add_argument("--no-resume", action="store_true")

    sub.add_parser("build-site", help="Build static site into dist/")
    sub.add_parser("approve-all", help="Approve all awaiting_approval articles and publish")
    sub.add_parser("backup", help="Create atomic SQLite backup")

    dash_p = sub.add_parser("dashboard", help="Start local FastAPI dashboard")
    dash_p.add_argument("--host", default="127.0.0.1")
    dash_p.add_argument("--port", type=int, default=8080)

    args = parser.parse_args()
    root = Path.cwd()
    settings = load_settings(root / "config" / "settings.yaml")
    db = Database(root / "data" / "autopilot.db")

    if args.cmd == "run-all":
        mgr = ManagerAgent(db=db, settings=settings, work_dir=root)
        res = mgr.run_all(
            csv_path=args.csv if args.csv.exists() else None,
            resume=not args.no_resume,
            max_articles=args.max_articles,
        )
        print(json.dumps(res, indent=2))
    elif args.cmd == "approve-all":
        for art in db.list_articles(status="awaiting_approval"):
            db.set_article_status(art.slug, "published")
        print(json.dumps(StaticBlogBuilder(db, settings, root).build(), indent=2))
    elif args.cmd == "build-site":
        print(json.dumps(StaticBlogBuilder(db, settings, root).build(), indent=2))
    elif args.cmd == "backup":
        print(str(db.backup(root / "data" / "backups")))
    elif args.cmd == "dashboard":
        uvicorn.run(create_app(root), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
