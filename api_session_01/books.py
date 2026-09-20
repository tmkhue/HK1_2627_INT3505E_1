from flask import Flask, jsonify, request, make_response
import sqlite3
app = Flask(__name__)
DB_FILE = "books.db"
_next_id = 1
DEFAULT_SIZE, MAX_SIZE = 20, 100

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS books (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        author TEXT NOT NULL
                    )""")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                quantity INTEGER,
                FOREIGN KEY (book_id) REFERENCES books (id)
            )
        """)
        
        cursor = conn.execute("SELECT COUNT(*) FROM books")
        if cursor.fetchone()[0] == 0:
            sample_books = [
                ("Clean code", "Martin"),
                ("Hello World", "Khue"),
                ("Fairy Princess", "Cho Miyeon")
            ]
            conn.executemany("INSERT INTO books (title, author) VALUES (?, ?)", sample_books)
            
            sample_orders = [
                (1, 2),
                (2, 1)
            ]
            conn.executemany("INSERT INTO orders (book_id, quantity) VALUES (?, ?)", sample_orders)
            conn.commit()

init_db()

# ─── GET /books —— trả danh sách
@app.get("/books")
def list_books():
    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size",DEFAULT_SIZE))
    except ValueError:
        return jsonify(error="So trang phai la so nguyen"), 400

    page = max(page, 1)
    size = max(min(size, MAX_SIZE), 1)

    query = "SELECT id, title, author FROM books Where 1=1"
    params = []

    a = request.args.get("author")
    if a:
        query += " AND LOWER(author) = LOWER(?)"
        params.append(a)
    q = (request.args.get("q")or"").lower()
    if q:
        query += " AND LOWER(title) LIKE LOWER(?)"
        params.append(f"%{q}%")
    if not params:
        return jsonify(error="Khong tim thay"), 404

    with get_db() as conn:
        count_query = f"SELECT COUNT(*) FROM ({query})"
        total = conn.execute(count_query, params).fetchone()[0]
        start = (page - 1)*size
        query += " LIMIT ? OFFSET ?"
        params.extend([size, start])
        cursor = conn.execute(query, params)
        items = [dict(row) for row in cursor.fetchall()]

    last =(total+size-1)//size

    #HATEOAS: tạo đường link và dẫn tới nó theo từng phần
    def u(p):
        return f"/books?page={p}&size={size}"
    links = {"self":{"href":u(page)},
             "first":{"href":u(1)},
             "last":{"href":max(last, 1)}}
    if page > 1:
        links["prev"]={"href":u(page-1)}
    if page*size < total:
        links["next"] = {"href":u(page+1)}
    body = {"data":items,
            "pagination":{"page":page,"size":size,"total":total,"total_pages":last},
            "_links":links}
    resp = make_response(jsonify(body), 200)
    resp.headers["Cache-Control"]="public, max-age=30"
    return resp

# ─── POST /books —— tạo mới
@app.post("/books")
def create_book():
    if not request.is_json:
        return jsonify(error="expected JSON"), 415
    p = request.get_json(silent=True) or {}
    t = (p.get("title") or"").strip()
    a = (p.get("author") or"").strip()
    if not t or not a:
        return jsonify(error="title and author required"), 422
    book = {"id": _next_id, "title": t, "author": a}
    with get_db() as conn:
        cursor = conn.execute("INSERT INTO books (title, author) VALUES (?, ?)", (t, a))
        conn.commit()
        book["id"] = cursor.lastrowid
    resp = make_response(jsonify(book), 201)
    resp.headers["Location"] = f"/books/{book['id']}"
    return resp

# ─── GET /books/<id> ─── cache 60s
@app.get("/books/<int:bid>")
def fetch(bid):
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, title, author FROM books WHERE id = ?", (bid,)
        ).fetchone()
    if row is None:
        return jsonify(error="not found"), 404
    resp = make_response(jsonify(dict(row)), 200)
    resp.headers["Cache-Control"]="max-age=60"
    return resp

# ─── PUT ─── thay toàn bộ, title+author bắt buộc
@app.put("/books/<int:bid>")
def put(bid):
    p = request.get_json(silent=True) or {}
    t, a = p.get("title"), p.get("author")
    if not t or not a:
        return jsonify(error="need title+author"), 422
    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE books SET title = ?, author = ? WHERE id = ?",
            (t.strip(), a.strip(), bid),
        )
        if cursor.rowcount == 0:
            return jsonify(error="not found"), 404
        row = conn.execute(
            "SELECT id, title, author FROM books WHERE id = ?", (bid,)
        ).fetchone()
    return jsonify(dict(row)), 200

# ─── PATCH ─── chỉ cập nhật field có trong body
@app.patch("/books/<int:bid>")
def patch(bid):
    p = request.get_json(silent=True) or {}
    fields = {k: p[k] for k in ("title", "author") if k in p}
    if "title" in fields:
        fields["title"] = str(fields["title"]).strip()
    if "author" in fields:
        fields["author"] = str(fields["author"]).strip()
    if any(not value for value in fields.values()):
        return jsonify(error="title and author cannot be empty"), 422
    with get_db() as conn:
        row = conn.execute("SELECT id FROM books WHERE id = ?", (bid,)).fetchone()
        if row is None:
            return jsonify(error="not found"), 404
        if fields:
            assignments = ", ".join(f"{key} = ?" for key in fields)
            conn.execute(
                f"UPDATE books SET {assignments} WHERE id = ?",
                (*fields.values(), bid),
            )
        row = conn.execute(
            "SELECT id, title, author FROM books WHERE id = ?", (bid,)
        ).fetchone()
    return jsonify(dict(row)), 200

# ─── DELETE ─── idempotent, trả 204
@app.delete("/books/<int:bid>")
def delete(bid):
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM books WHERE id = ?", (bid,))
    if cursor.rowcount == 0:
        return jsonify(error="not found"), 404
    return "", 204

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)