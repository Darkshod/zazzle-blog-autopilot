"""DARKSHOD Executive Business Control Center (FastAPI Dashboard & Action API)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from .agents.manager import ManagerAgent
from .config import AppSettings, load_settings, validate_ga4_measurement_id
from .db import Database
from .models import utc_now_iso
from .integrations.gsc import GoogleSearchConsoleClient
from .integrations.pinterest_api import prioritize_top_pins
from .site_builder import StaticBlogBuilder


def create_app(root_dir: Path | None = None) -> FastAPI:
    work_dir = root_dir or Path.cwd()
    settings: AppSettings = load_settings(work_dir / "config" / "settings.yaml")
    db = Database(work_dir / "data" / "autopilot.db")
    mgr = ManagerAgent(db=db, settings=settings, work_dir=work_dir)
    builder = StaticBlogBuilder(db=db, settings=settings, root_dir=work_dir)

    app = FastAPI(title="DARKSHOD — Master Business Control Center", version="2.0.0")

    @app.get("/", response_class=HTMLResponse)
    def dashboard_home() -> str:
        metrics = db.get_dashboard_metrics()
        fin = db.get_financial_summary()
        articles = db.list_articles()
        tasks = db.list_executive_tasks()[:10]
        seo_report = mgr.seo_doctor.run(dist_dir=work_dir / "dist").output_summary
        emergency = db.get_system_flag("emergency_stop") == "true"

        gsc_status = "CONNECTED" if os.getenv("GSC_ACCESS_TOKEN") else "NOT CONNECTED"
        ga4_status = "CONNECTED" if os.getenv("GA4_MEASUREMENT_ID") else "NOT CONNECTED"
        pin_status = "CONNECTED" if os.getenv("PINTEREST_ACCESS_TOKEN") else "NOT CONNECTED"
        aff_status = "ACTIVE" if settings.monetization.zazzle_affiliate_approved else "NOT VERIFIED"

        article_rows = "".join(
            f"""<tr>
              <td>{a.title}</td>
              <td>{a.category}</td>
              <td>{a.word_count}</td>
              <td>{a.qa_score}/100</td>
              <td><span class="pill">{a.status}</span></td>
              <td><button onclick="postAction('/api/articles/{a.slug}/approve')">Approve</button></td>
            </tr>"""
            for a in articles[:15]
        )
        task_rows = "".join(
            f"<tr><td>{t['task_id']}</td><td>{t['assigned_agent']}</td><td>{t['status']}</td><td>{t['business_impact']}</td></tr>"
            for t in tasks
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>DARKSHOD — Executive Business Control Center</title>
  <style>
    body{{font-family:system-ui,sans-serif;background:#f7f5f0;color:#1b221e;margin:0;padding:1.5rem}}
    .wrap{{max-width:1220px;margin:0 auto}}
    h1{{margin:0 0 .25rem}}
    .sub{{color:#5b635e;margin-bottom:1rem}}
    .badges{{display:flex;flex-wrap:wrap;gap:.5rem;margin-bottom:1.25rem}}
    .badge{{padding:.3rem .75rem;border-radius:999px;font-size:.78rem;font-weight:700;background:#ece6da}}
    .actions{{display:flex;flex-wrap:wrap;gap:.55rem;margin-bottom:1.5rem}}
    button{{padding:.55rem .95rem;border:1px solid #22382c;background:#22382c;color:#fff;border-radius:8px;cursor:pointer;font-weight:600}}
    button.danger{{background:#8c2a2e;border-color:#8c2a2e}}
    .cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(175px,1fr));gap:.9rem;margin-bottom:1.5rem}}
    .card{{background:#fff;border:1px solid #e5dfd4;border-radius:10px;padding:.95rem}}
    .num{{font-size:1.45rem;font-weight:700;color:#22382c}}
    .lbl{{font-size:.75rem;color:#5b635e;text-transform:uppercase;letter-spacing:.06em}}
    table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e5dfd4;margin-bottom:1.5rem}}
    th,td{{padding:.6rem .75rem;border-bottom:1px solid #eee;text-align:left;font-size:.88rem}}
    .pill{{padding:.2rem .55rem;border-radius:999px;background:#efeae1;font-size:.78rem}}
    pre{{background:#1b221e;color:#e7f3ec;padding:1rem;border-radius:8px;overflow:auto;max-height:220px}}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>DARKSHOD — Master Business Control Center</h1>
    <p class="sub">Market: {settings.brand.primary_market} &middot; Top Bottleneck: {mgr.identify_top_bottleneck()}</p>

    <div class="badges">
      <span class="badge">GSC: {gsc_status}</span>
      <span class="badge">GA4: {ga4_status}</span>
      <span class="badge">Pinterest API v5: {pin_status}</span>
      <span class="badge">Zazzle Affiliate: {aff_status}</span>
      <span class="badge">Emergency Stop: {'ACTIVE' if emergency else 'OFF'}</span>
    </div>

    <div class="actions">
      <button onclick="postAction('/api/run-all')">Run All Agents</button>
      <button onclick="postAction('/api/find-keywords')">Run Research</button>
      <button onclick="postAction('/api/generate-articles')">Generate Articles</button>
      <button onclick="postAction('/api/run-seo-audit')">Run SEO Audit</button>
      <button onclick="postAction('/api/generate-pins')">Generate Pinterest Campaign</button>
      <button onclick="postAction('/api/publish-approved')">Publish Approved Content</button>
      <button onclick="postAction('/api/run-weekly-report')">Run Weekly Report</button>
      <button class="danger" onclick="postAction('/api/emergency-stop?active={'false' if emergency else 'true'}')">{'Resume System' if emergency else 'Emergency Stop'}</button>
    </div>

    <div class="cards">
      <div class="card"><div class="num">{metrics['total_products']}</div><div class="lbl">Zazzle Products</div></div>
      <div class="card"><div class="num">{metrics['articles_published']} / {metrics['articles_generated']}</div><div class="lbl">Published / Total</div></div>
      <div class="card"><div class="num">{metrics['target_keywords']}</div><div class="lbl">Target Keywords</div></div>
      <div class="card"><div class="num">{metrics['pinterest_pins']}</div><div class="lbl">Pinterest Queue</div></div>
      <div class="card"><div class="num">{metrics['product_outbound_clicks']}</div><div class="lbl">Product Clicks</div></div>
      <div class="card"><div class="num">{metrics['affiliate_clicks']}</div><div class="lbl">Affiliate Clicks</div></div>
      <div class="card"><div class="num">${fin['net_profit_usd']:.2f}</div><div class="lbl">Verified Net ({fin['status_label'][:12]})</div></div>
      <div class="card"><div class="num">{'HEALTHY' if seo_report.get('healthy') else 'NEEDS BUILD'}</div><div class="lbl">SEO Health</div></div>
    </div>

    <h2>Content &amp; Approval Queue</h2>
    <table><thead><tr><th>Title</th><th>Category</th><th>Words</th><th>QA</th><th>Status</th><th>Action</th></tr></thead><tbody>{article_rows or '<tr><td colspan="6">No articles yet.</td></tr>'}</tbody></table>

    <h2>Executive Task Ledger (17-Agent Team)</h2>
    <table><thead><tr><th>Task ID</th><th>Agent</th><th>Status</th><th>Impact</th></tr></thead><tbody>{task_rows or '<tr><td colspan="4">Run All Agents to populate task ledger.</td></tr>'}</tbody></table>

    <pre id="out">Ready.</pre>
  </div>
  <script>
    async function postAction(url) {{
      const out = document.getElementById('out');
      out.textContent = 'Running ' + url + '...';
      const res = await fetch(url, {{method: 'POST'}});
      out.textContent = JSON.stringify(await res.json(), null, 2);
      setTimeout(() => location.reload(), 800);
    }}
  </script>
</body>
</html>"""

    @app.get("/api/metrics")
    def api_metrics() -> JSONResponse:
        return JSONResponse({"business": db.get_dashboard_metrics(), "financial": db.get_financial_summary()})

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
        res = mgr.pinterest_agent.run().model_dump()
        top20 = prioritize_top_pins(db.list_pins(), limit=20)
        res["top20_count"] = len(top20)
        return JSONResponse(res)

    @app.post("/api/articles/{slug}/approve")
    def api_approve_article(slug: str) -> JSONResponse:
        if slug not in {a.slug for a in db.list_articles()}:
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

    @app.post("/api/run-weekly-report")
    def api_weekly_report() -> JSONResponse:
        gsc = GoogleSearchConsoleClient(settings.brand.base_url).fetch_search_analytics()
        fin = mgr.financial_agent.run().model_dump()
        mon = mgr.monetization_agent.run(dist_dir=work_dir / "dist").model_dump()
        return JSONResponse({"gsc": gsc, "financial": fin, "monetization": mon, "metrics": db.get_dashboard_metrics()})

    @app.post("/api/emergency-stop")
    def api_emergency_stop(active: bool = True) -> JSONResponse:
        db.set_system_flag("emergency_stop", "true" if active else "false")
        return JSONResponse({"emergency_stop": active})

    def _load_pin_state() -> dict:
        p = work_dir / "pinterest_approval_state.json"
        if not p.exists():
            return {"account": "@rafafo1225", "total_pins": 0, "batch_authorized": False, "audit_log": [], "pins": []}
        return json.loads(p.read_text(encoding="utf-8"))

    def _save_pin_state(state: dict) -> None:
        (work_dir / "pinterest_approval_state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")

    @app.get("/pinterest-gallery", response_class=HTMLResponse)
    def pinterest_gallery_page() -> str:
        gp = work_dir / "pinterest_approval_gallery.html"
        if not gp.exists():
            return "<h1>Gallery not built yet. Run scripts/build_pinterest_approval_system.py</h1>"
        return gp.read_text(encoding="utf-8")

    @app.get("/api/pinterest/summary")
    def api_pinterest_summary() -> JSONResponse:
        st = _load_pin_state()
        pins = st.get("pins", [])
        return JSONResponse({
            "account": st.get("account", "@rafafo1225"),
            "total_pins": len(pins),
            "individually_verified_urls": sum(1 for p in pins if p.get("url_http_status") == 200),
            "pending_approval": sum(1 for p in pins if p.get("decision") == "pending_approval"),
            "approved": sum(1 for p in pins if p.get("decision") == "approved"),
            "rejected": sum(1 for p in pins if p.get("decision") == "rejected"),
            "needs_edit": sum(1 for p in pins if p.get("decision") == "needs_edit"),
            "published": sum(1 for p in pins if p.get("decision") == "published"),
            "batch_authorized": st.get("batch_authorized", False),
        })

    @app.post("/api/pinterest/decision")
    def api_pinterest_decision(payload: dict = Body(...)) -> JSONResponse:
        pin_number = int(payload.get("pin_number", 0))
        decision = str(payload.get("decision", ""))
        if decision not in ("approved", "rejected", "needs_edit", "pending_approval"):
            raise HTTPException(status_code=400, detail="Invalid decision")
        st = _load_pin_state()
        found = False
        for p in st.get("pins", []):
            if p.get("pin_number") == pin_number:
                p["decision"] = decision
                p["edit_note"] = str(payload.get("edit_note", ""))
                found = True
                break
        if not found:
            raise HTTPException(status_code=404, detail="Pin not found")
        st.setdefault("audit_log", []).append({"ts": utc_now_iso(), "action": "decision", "pin_number": pin_number, "decision": decision})
        _save_pin_state(st)
        return JSONResponse({"pin_number": pin_number, "decision": decision})

    @app.post("/api/pinterest/authorize-batch")
    def api_pinterest_authorize_batch() -> JSONResponse:
        st = _load_pin_state()
        pins = st.get("pins", [])
        approved_pins = [p for p in pins if p.get("decision") == "approved"]
        if not approved_pins:
            raise HTTPException(status_code=400, detail="No individually approved pins to authorize.")
        st["batch_authorized"] = True
        st.setdefault("audit_log", []).append({"ts": utc_now_iso(), "action": "batch_authorized", "approved_count": len(approved_pins)})
        _save_pin_state(st)
        return JSONResponse({
            "batch_authorized": True,
            "approved_count": len(approved_pins),
            "excluded_rejected": sum(1 for p in pins if p.get("decision") == "rejected"),
            "excluded_needs_edit": sum(1 for p in pins if p.get("decision") == "needs_edit"),
            "excluded_pending": sum(1 for p in pins if p.get("decision") == "pending_approval"),
        })

    @app.get("/api/integration-status")
    def api_integration_status() -> JSONResponse:
        ga4_ok = validate_ga4_measurement_id(settings.brand.ga4_measurement_id)
        gsc_token_ok = bool(os.getenv("GSC_ACCESS_TOKEN"))
        gsc_meta_ok = bool(settings.brand.gsc_verification_token)
        seo_res = mgr.seo_doctor.run(dist_dir=work_dir / "dist").output_summary
        pin_sum = json.loads(api_pinterest_summary().body.decode("utf-8"))
        return JSONResponse({
            "google_analytics": {
                "status": "CONFIGURED" if ga4_ok else "NOT CONFIGURED",
                "live_events_verified": False,
            },
            "google_search_console": {
                "status": "API CONNECTED" if gsc_token_ok else "NOT CONFIGURED",
                "ownership_verified": False,
                "verification_tag_configured": gsc_meta_ok,
                "sitemap_submitted": False,
                "performance_data_available": False,
            },
            "pinterest": pin_sum,
            "website": {
                "article_count": len(db.list_articles(status="published")) + len(db.list_articles(status="approved")),
                "sitemap_healthy": seo_res.get("sitemap_valid", False),
                "broken_links": len([i for i in seo_res.get("issues", []) if "broken" in i]),
                "healthy": seo_res.get("healthy", False),
            },
        })

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
