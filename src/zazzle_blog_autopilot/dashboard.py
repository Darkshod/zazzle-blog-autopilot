"""FastAPI Dashboard & Action API — every button executes its real agent or pipeline action."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from .agents.manager import ManagerAgent
from .config import AppSettings, load_settings
from .db import Database
from .site_builder import StaticBlogBuilder


def create_app(root_dir: Path | None = None) -> FastAPI:
    work_dir = root_dir or Path.cwd()
    settings: AppSettings = load_settings(work_dir / "config" / "settings.yaml")
    db = Database(work_dir / "data" / "autopilot.db")
    mgr = ManagerAgent(db=db, settings=settings, work_dir=work_dir)
    builder = StaticBlogBuilder(db=db, settings=settings, root_dir=work_dir)

    app = FastAPI(title="Zazzle Blog Autopilot Dashboard", version="1.0.0")

    @app.get("/", response_class=HTMLResponse)
    def dashboard_home() -> str:
        metrics = db.get_dashboard_metrics()
        articles = db.list_articles()
        logs = db.list_agent_logs(limit=12)
        seo_report = mgr.seo_doctor.run(dist_dir=work_dir / "dist").output_summary

        article_rows = "".join(
            f"""<tr>
              <td>{a.title}</td>
              <td>{a.category}</td>
              <td>{a.word_count}</td>
              <td>{a.qa_score}/100</td>
              <td><span class="pill">{a.status}</span></td>
              <td><button onclick="postAction('/api/articles/{a.slug}/approve')">Approve</button></td>
            </tr>"""
            for a in articles[:20]
        )
        log_rows = "".join(
            f"<tr><td>{l['agent_name']}</td><td>{l['task']}</td><td>{l['status']}</td><td>{l['timestamp'][:19]}</td></tr>"
            for l in logs
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Zazzle Blog Autopilot — Control Dashboard</title>
  <style>
    body{{font-family:system-ui,sans-serif;background:#f7f5f0;color:#1b221e;margin:0;padding:1.5rem}}
    .wrap{{max-width:1180px;margin:0 auto}}
    h1{{margin:0 0 .3rem}}
    .sub{{color:#5b635e;margin-bottom:1.25rem}}
    .actions{{display:flex;flex-wrap:wrap;gap:.6rem;margin-bottom:1.5rem}}
    button{{padding:.58rem 1rem;border:1px solid #22382c;background:#22382c;color:#fff;border-radius:8px;cursor:pointer;font-weight:600}}
    button:hover{{background:#16261d}}
    .cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:1rem;margin-bottom:1.5rem}}
    .card{{background:#fff;border:1px solid #e5dfd4;border-radius:10px;padding:1rem}}
    .num{{font-size:1.65rem;font-weight:700;color:#22382c}}
    .lbl{{font-size:.8rem;color:#5b635e;text-transform:uppercase;letter-spacing:.06em}}
    table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e5dfd4;margin-bottom:1.5rem}}
    th,td{{padding:.65rem .8rem;border-bottom:1px solid #eee;text-align:left;font-size:.9rem}}
    .pill{{padding:.2rem .55rem;border-radius:999px;background:#efeae1;font-size:.78rem}}
    pre{{background:#1b221e;color:#e7f3ec;padding:1rem;border-radius:8px;overflow:auto;max-height:220px}}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Zazzle Blog Autopilot Dashboard</h1>
    <p class="sub">Market: {settings.brand.primary_market} &middot; Approval Required: {settings.publishing.require_human_approval} &middot; Affiliate Approved: {settings.monetization.zazzle_affiliate_approved}</p>

    <div class="actions">
      <button onclick="postAction('/api/run-all')">Run All Agents</button>
      <button onclick="postAction('/api/research-products')">Research Products</button>
      <button onclick="postAction('/api/find-keywords')">Find Keywords</button>
      <button onclick="postAction('/api/generate-articles')">Generate Articles</button>
      <button onclick="postAction('/api/run-seo-audit')">Run SEO Audit</button>
      <button onclick="postAction('/api/generate-pins')">Generate Pinterest Pins</button>
      <button onclick="postAction('/api/publish-approved')">Publish Approved Articles</button>
      <button onclick="postAction('/api/export-reports')">Export Reports</button>
    </div>

    <div class="cards">
      <div class="card"><div class="num">{metrics['total_products']}</div><div class="lbl">Zazzle Products</div></div>
      <div class="card"><div class="num">{metrics['articles_generated']}</div><div class="lbl">Articles Generated</div></div>
      <div class="card"><div class="num">{metrics['articles_published']}</div><div class="lbl">Articles Published</div></div>
      <div class="card"><div class="num">{metrics['articles_awaiting_approval']}</div><div class="lbl">Awaiting Approval</div></div>
      <div class="card"><div class="num">{metrics['target_keywords']}</div><div class="lbl">Target Keywords</div></div>
      <div class="card"><div class="num">{metrics['pinterest_pins']}</div><div class="lbl">Pinterest Pins</div></div>
      <div class="card"><div class="num">{metrics['product_outbound_clicks']}</div><div class="lbl">Outbound Clicks</div></div>
      <div class="card"><div class="num">{metrics['affiliate_clicks']}</div><div class="lbl">Affiliate Clicks</div></div>
      <div class="card"><div class="num">{'HEALTHY' if seo_report.get('healthy') else 'NEEDS BUILD'}</div><div class="lbl">SEO Health ({len(seo_report.get('issues', []))} issues)</div></div>
    </div>

    <p><strong>Organic Traffic:</strong> {metrics['organic_traffic']} &nbsp;|&nbsp; <strong>Verified Sales:</strong> {metrics['verified_sales_and_commissions']}</p>

    <h2>Articles Queue</h2>
    <table><thead><tr><th>Title</th><th>Category</th><th>Words</th><th>QA</th><th>Status</th><th>Action</th></tr></thead><tbody>{article_rows or '<tr><td colspan="6">No articles yet. Click Run All Agents.</td></tr>'}</tbody></table>

    <h2>Agent Activity Log</h2>
    <table><thead><tr><th>Agent</th><th>Task</th><th>Status</th><th>Timestamp</th></tr></thead><tbody>{log_rows or '<tr><td colspan="4">No logs yet.</td></tr>'}</tbody></table>

    <h3>Action Output</h3>
    <pre id="out">Click any button above to run an agent or export reports.</pre>
  </div>
  <script>
    async function postAction(url) {{
      const out = document.getElementById('out');
      out.textContent = 'Running ' + url + '...';
      const res = await fetch(url, {{method: 'POST'}});
      const data = await res.json();
      out.textContent = JSON.stringify(data, null, 2);
      setTimeout(() => location.reload(), 900);
    }}
  </script>
</body>
</html>"""

    @app.get("/api/metrics")
    def api_metrics() -> JSONResponse:
        return JSONResponse(db.get_dashboard_metrics())

    @app.post("/api/run-all")
    def api_run_all() -> JSONResponse:
        csv_path = work_dir / "data" / "sample_products.csv"
        return JSONResponse(mgr.run_all(csv_path=csv_path if csv_path.exists() else None, resume=False))

    @app.post("/api/research-products")
    def api_research_products() -> JSONResponse:
        csv_path = work_dir / "data" / "sample_products.csv"
        return JSONResponse(mgr.product_agent.run(csv_path=csv_path if csv_path.exists() else None).model_dump())

    @app.post("/api/find-keywords")
    def api_find_keywords() -> JSONResponse:
        mkt = mgr.market_agent.run(enable_live_autocomplete=False)
        kw = mgr.keyword_agent.run(market_trends=mkt.output_summary.get("trends", []))
        return JSONResponse(kw.model_dump())

    @app.post("/api/generate-articles")
    def api_generate_articles() -> JSONResponse:
        gen = mgr.content_agent.run(max_articles=4)
        qa = mgr.qa_agent.run()
        img = mgr.image_agent.run(output_dir=work_dir / "site" / "assets" / "generated")
        return JSONResponse({"content": gen.model_dump(), "qa": qa.model_dump(), "images": img.model_dump()})

    @app.post("/api/run-seo-audit")
    def api_run_seo_audit() -> JSONResponse:
        return JSONResponse(mgr.seo_doctor.run(dist_dir=work_dir / "dist").model_dump())

    @app.post("/api/generate-pins")
    def api_generate_pins() -> JSONResponse:
        return JSONResponse(mgr.pinterest_agent.run().model_dump())

    @app.post("/api/articles/{slug}/approve")
    def api_approve_article(slug: str) -> JSONResponse:
        articles = {a.slug: a for a in db.list_articles()}
        if slug not in articles:
            raise HTTPException(status_code=404, detail="Article not found")
        db.set_article_status(slug, "approved")
        return JSONResponse({"slug": slug, "status": "approved"})

    @app.post("/api/publish-approved")
    def api_publish_approved() -> JSONResponse:
        approved = db.list_articles(status="approved")
        for a in approved:
            db.set_article_status(a.slug, "published")
        build_res = builder.build(include_approved=True)
        seo_res = mgr.seo_doctor.run(dist_dir=work_dir / "dist").model_dump()
        return JSONResponse({"published_count": len(approved), "build": build_res, "seo_audit": seo_res})

    @app.post("/api/export-reports")
    def api_export_reports() -> JSONResponse:
        export_dir = work_dir / "reports" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        metrics = db.get_dashboard_metrics()
        backup_path = db.backup(work_dir / "data" / "backups")
        report_file = export_dir / "autopilot_report.json"
        report_file.write_text(json.dumps({"metrics": metrics, "backup": str(backup_path)}, indent=2), encoding="utf-8")
        return JSONResponse({"report_file": str(report_file), "backup": str(backup_path), "metrics": metrics})

    @app.post("/api/track-click")
    def api_track_click(
        event_type: str = "outbound_product",
        article_slug: str = "home",
        product_id: int | None = None,
        is_affiliate: bool = False,
        destination_url: str = "",
    ) -> JSONResponse:
        db.record_click(event_type, article_slug, product_id, is_affiliate, destination_url)
        return JSONResponse({"recorded": True})

    return app
