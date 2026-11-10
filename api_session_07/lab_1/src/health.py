from flask import Blueprint, jsonify
from sqlalchemy import text
from .extensions import db
health_bp = Blueprint("health", __name__, url_prefix="")
# liveness — không DB
@health_bp.get("/healthz")
def liveness():
    return jsonify({"status": "healthy"})

# readiness — có DB
@health_bp.get("/ready")
def readiness():
    checks = {}
    try:
        db.session.query(text("1")).from_self().all()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        ok = all(v == "ok" for v in checks.values())
    return jsonify({"status": "ready" if all(v == "ok" for v in checks.values()) else "not ready", "checks": checks}), 200 if all(v == "ok" for v in checks.values()) else 503