import html
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models import Check, Target

LABELS = {"up": "Opérationnel", "down": "Hors service", "unknown": "En attente"}
COLORS = {"up": "#16a34a", "down": "#dc2626", "unknown": "#6b7280"}

PAGE = """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="30">
  <title>StatusWatch</title>
  <style>
    body { font-family: system-ui, sans-serif; background: #f8fafc; color: #0f172a; margin: 0; }
    main { max-width: 640px; margin: 0 auto; padding: 40px 20px; }
    h1 { margin: 0 0 20px; }
    .banner { padding: 16px 20px; border-radius: 12px; color: white; font-weight: 600; }
    ul { list-style: none; padding: 0; margin: 24px 0 0; }
    li { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px 20px;
         margin-bottom: 12px; display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
    .dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
    .name { font-weight: 600; flex: 1; }
    .meta { color: #64748b; font-size: 14px; }
    footer { color: #94a3b8; font-size: 13px; margin-top: 24px; }
  </style>
</head>
<body>
  <main>
    <h1>StatusWatch</h1>
    <div class="banner" style="background: __BANNER_COLOR__">__BANNER__</div>
    <ul>__ROWS__</ul>
    <footer>Mise à jour automatique toutes les 30 secondes.</footer>
  </main>
</body>
</html>"""


def build_status(db: Session) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    items = []
    for target in db.scalars(select(Target).order_by(Target.id)):
        last = db.scalars(
            select(Check)
            .where(Check.target_id == target.id)
            .order_by(Check.id.desc())
            .limit(1)
        ).first()

        total, up = db.execute(
            select(func.count(Check.id), func.sum(case((Check.is_up, 1), else_=0)))
            .where(Check.target_id == target.id, Check.checked_at >= since)
        ).one()

        items.append(
            {
                "id": target.id,
                "name": target.name,
                "status": "unknown" if last is None else ("up" if last.is_up else "down"),
                "response_ms": None if last is None else last.response_ms,
                "last_checked": None if last is None else last.checked_at,
                "uptime_24h": round(100 * (up or 0) / total, 2) if total else None,
            }
        )
    return items


def render_page(items: list[dict]) -> str:
    rows = ""
    for item in items:
        uptime = "—" if item["uptime_24h"] is None else f"{item['uptime_24h']} %"
        response = "—" if item["response_ms"] is None else f"{item['response_ms']} ms"
        rows += (
            "<li>"
            f'<span class="dot" style="background: {COLORS[item["status"]]}"></span>'
            # Le nom vient de l'utilisateur : toujours l'échapper avant de l'afficher
            f'<span class="name">{html.escape(item["name"])}</span>'
            f'<span class="meta">{LABELS[item["status"]]} · {response} · {uptime} sur 24 h</span>'
            "</li>"
        )

    if not items:
        banner, color = "Aucun service surveillé pour le moment", COLORS["unknown"]
    elif any(item["status"] == "down" for item in items):
        banner, color = "Incident en cours", COLORS["down"]
    elif all(item["status"] == "up" for item in items):
        banner, color = "Tous les systèmes sont opérationnels", COLORS["up"]
    else:
        banner, color = "Vérifications en cours", COLORS["unknown"]

    return (
        PAGE.replace("__BANNER_COLOR__", color)
        .replace("__BANNER__", banner)
        .replace("__ROWS__", rows)
    )