"""Social Network API matching openapi_spec.yaml."""

from datetime import timedelta
from email.utils import parseaddr
from functools import wraps
import os
import re
import sqlite3
import time
from threading import Lock

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError
from flask import Flask, g, jsonify, request
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ["FLASK_SECRET_KEY"],
    JWT_SECRET_KEY=os.environ["JWT_SECRET_KEY"],
    JWT_ALGORITHM="HS256",
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(seconds=900),
    JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=30),
)
jwt = JWTManager(app)

DB_NAME = os.environ.get("DATABASE_PATH", "app.db")
password_hasher = PasswordHasher(type=Type.ID)

# Lightweight per-process rate limits. Use a shared store such as Redis when
# running multiple workers or instances.
_rate_lock = Lock()
_rate_buckets = {}

def problem(status, title, detail):
    response = jsonify({
        "type": "about:blank",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": request.path,
    })
    response.status_code = status
    response.content_type = "application/problem+json"
    return response

# giới hạn số lượng request
def rate_limit(limit, window_seconds=60):
    def decorate(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            now = time.monotonic()
            key = (request.endpoint, request.remote_addr or "unknown")
            with _rate_lock:
                timestamps = [t for t in _rate_buckets.get(key, []) if now - t < window_seconds]
                if len(timestamps) >= limit:
                    _rate_buckets[key] = timestamps
                    return problem(429, "Too Many Requests", "Rate limit exceeded.")
                timestamps.append(now)
                _rate_buckets[key] = timestamps
            return view(*args, **kwargs)
        return wrapped
    return decorate

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_NAME)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

# Dọn dẹp tài nguyên kết nối cơ sở dữ liệu khi 1 http request kết thúc, bất kể thành công hay thất bại
@app.teardown_appcontext
def close_db(_exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                pwd_hash TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                scopes TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
                PRIMARY KEY (user_id, role_id)
            );
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                author_id INTEGER NOT NULL REFERENCES users(id),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                likes_count INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS revoked_tokens (
                jti TEXT PRIMARY KEY,
                revoked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Demo account: admin@example.com / admin123
        db.execute("INSERT OR IGNORE INTO roles (id, name, scopes) VALUES (?, ?, ?)",
                   (1, "admin", "auth:refresh,posts:read"))
        db.execute("INSERT OR IGNORE INTO roles (id, name, scopes) VALUES (?, ?, ?)",
                   (2, "user", "auth:refresh,posts:read"))
        existing = db.execute("SELECT id FROM users WHERE email = ?", ("admin@example.com",)).fetchone()
        if existing is None:
            pwd_hash = password_hasher.hash("admin123")
            cursor = db.execute("INSERT INTO users (email, pwd_hash) VALUES (?, ?)",
                                ("admin@example.com", pwd_hash))
            user_id = cursor.lastrowid
        else:
            user_id = existing["id"]
        db.execute("INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, 1)", (user_id,))
        db.execute("INSERT OR IGNORE INTO posts (id, author_id, content, likes_count) VALUES (?, ?, ?, ?)",
                   ("post_99a8b7c6", user_id, "Hôm nay thời tiết thật đẹp!", 42))
        db.commit()

def user_permissions(user_id):
    rows = get_db().execute("""
        SELECT r.name, r.scopes FROM roles r
        JOIN user_roles ur ON ur.role_id = r.id
        WHERE ur.user_id = ?
    """, (user_id,)).fetchall()
    roles, scopes = set(), set()
    for row in rows:
        roles.add(row["name"])
        scopes.update(scope.strip() for scope in row["scopes"].split(",") if scope.strip())
    return sorted(roles), sorted(scopes)

# Kích hoạt khi client gửi đến route yêu cầu đăng nhập nhưng không có Authorization header, token
@jwt.unauthorized_loader
def missing_token(_reason):
    return problem(401, "Unauthorized", "A bearer token is required.")

# kích hoạt khi client gửi đến route yêu cầu đăng nhập nhưng token không hợp lệ
@jwt.invalid_token_loader
def invalid_token(reason):
    # flask-jwt-extended reports an access token used on a refresh-only route
    # as an invalid token; the API contract classifies that as forbidden.
    if "refresh token" in reason.lower() or "only refresh" in reason.lower():
        return problem(403, "Forbidden", "A refresh token is required for this endpoint.")
    return problem(401, "Unauthorized", "Token is invalid.")

@jwt.expired_token_loader
def expired_token(_header, _payload):
    return problem(401, "Unauthorized", "Token has expired.")

# tự động chạy mỗi khi client gửi 1 token hợp lệ đến endpoint có bảo vệ
@jwt.token_in_blocklist_loader
def is_token_revoked(_header, payload):
    return get_db().execute(
        "SELECT 1 FROM revoked_tokens WHERE jti = ?", (payload.get("jti"),)
    ).fetchone() is not None

def revoke_token(jti):
    """Revoke a JWT by its jti; call this from logout or account-disable flows."""
    get_db().execute("INSERT OR IGNORE INTO revoked_tokens (jti) VALUES (?)", (jti,))
    get_db().commit()

# kiểm tra người dùng có đc cấp quyền (scope: delete, read, write,...)
def require_scope(scope):
    def decorate(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if scope not in get_jwt().get("scopes", []):
                return problem(403, "Forbidden", f"Required scope: {scope}")
            return view(*args, **kwargs)
        return wrapped
    return decorate

# đảm bảo dữ liệu gửi lên là JSON object
def parse_json_object():
    if not request.is_json:
        return None, problem(400, "Bad Request", "Request body must be JSON.")
    try:
        data = request.get_json(silent=False)
    except Exception:
        return None, problem(400, "Bad Request", "Malformed JSON request body.")
    if not isinstance(data, dict):
        return None, problem(400, "Bad Request", "JSON request body must be an object.")
    return data, None

def valid_email(value):
    if not isinstance(value, str) or len(value) > 254:
        return False
    return parseaddr(value)[1] == value and bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value))

@app.post("/v1/auth/login")
@rate_limit(10)
def login():
    data, error = parse_json_object()
    if error:
        return error
    email, password = data.get("email"), data.get("password")
    if not valid_email(email) or not isinstance(password, str) or not password:
        return problem(422, "Validation Error", "A valid email and non-empty password are required.")

    user = get_db().execute(
        "SELECT id, pwd_hash, is_active FROM users WHERE email = ?", (email.lower(),)
    ).fetchone()
    if user is None or not user["is_active"]:
        return problem(401, "Unauthorized", "Invalid email or password.")
    try:
        password_ok = password_hasher.verify(user["pwd_hash"], password)
    except (VerificationError, InvalidHashError):
        password_ok = False
    if not password_ok:
        return problem(401, "Unauthorized", "Invalid email or password.")

    roles, scopes = user_permissions(user["id"])
    access = create_access_token(
        identity=str(user["id"]), additional_claims={"roles": roles, "scopes": scopes}
    )
    refresh = create_refresh_token(
        identity=str(user["id"]),
        additional_claims={"roles": roles, "scopes": ["auth:refresh"]},
    )
    return jsonify(access_token=access, refresh_token=refresh,
                   token_type="Bearer", expires_in=900), 200

@app.post("/v1/auth/refresh")
@rate_limit(30)
@jwt_required(refresh=True)
@require_scope("auth:refresh")
def refresh_token():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return problem(401, "Unauthorized", "Invalid token identity.")
    user = get_db().execute("SELECT is_active FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None or not user["is_active"]:
        return problem(401, "Unauthorized", "Token user is not active.")
    roles, scopes = user_permissions(user_id)
    access = create_access_token(
        identity=str(user_id), additional_claims={"roles": roles, "scopes": scopes}
    )
    return jsonify(access_token=access, token_type="Bearer", expires_in=900), 200

@app.get("/v1/posts/<string:post_id>")
@jwt_required()
@require_scope("posts:read")
def get_post(post_id):
    post = get_db().execute("""
        SELECT id, author_id, content, created_at, likes_count
        FROM posts WHERE id = ?
    """, (post_id,)).fetchone()
    if post is None:
        return problem(404, "Not Found", "Post not found.")
    return jsonify({
        "id": post["id"],
        "author_id": str(post["author_id"]),
        "content": post["content"],
        "created_at": post["created_at"],
        "likes_count": post["likes_count"],
    }), 200

@app.errorhandler(500)
def internal_error(_error):
    return problem(500, "Internal Server Error", "An unexpected server error occurred.")

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
