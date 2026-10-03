from datetime import datetime
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
import uuid

ERROR_BASE = "https://example.com/problems"

class ApiProblem(Exception):
    def __init__(self, status, title, detail=None, type_path=None, **extra):
        self.status = status
        self.title = title
        self.detail = detail
        self.type_path = type_path
        self.extra = extra

def _problem(status, title, detail=None, type_path=None, **extra):
    body = {
        "type": f"{ERROR_BASE}/{type_path}" if type_path is not None else "about:blank",
        "title": title,
        "status": status,
        "instance": request.path,
        "trace_id": str(uuid.uuid4()),
    }
    if detail is not None:
        body["detail"] = detail
    body.update(extra)
    response = jsonify(body)
    response.status_code = status
    response.headers["Content-Type"] = "application/problem+json"
    return response

app = Flask(__name__)
USERS = [
    {"id": 1, "name": "Tran Minh A", "bio": "", "followers": [], "following": []},
    {"id": 2, "name": "Nguyen Van B", "bio": "", "followers": [], "following": []},
    {"id": 3, "name": "Le Minh C", "bio": "", "followers": [], "following": []},
    {"id": 4, "name": "Pham Van D", "bio": "", "followers": [], "following": []},
]
POSTS = []
COMMENTS = []
_next_ids = {"user": 5, "post": 1, "comment": 1}
def find_user(user_id):
    return next((user for user in USERS if user["id"] == int(user_id)), None)

def find_post(post_id):
    return next((post for post in POSTS if post["id"] == int(post_id)), None)

def find_comment(comment_id):
    return next((comment for comment in COMMENTS if comment["id"] == int(comment_id)), None)

def error(message, status):
    raise ApiProblem(status=status, title=_status_title(status), detail=message)

def _status_title(status):
    titles = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        415: "Unsupported Media Type",
        422: "Unprocessable Content",
        429: "Too Many Requests",
        500: "Internal Server Error",
    }
    return titles.get(status, "HTTP Error")

@app.errorhandler(ApiProblem)
def handle_api_problem(problem):
    return _problem(
        status=problem.status,
        title=problem.title,
        detail=problem.detail,
        type_path=problem.type_path,
        **problem.extra,
    )

@app.errorhandler(HTTPException)
def handle_http_exception(exception):
    return _problem(
        status=exception.code or 500,
        title=exception.name,
        detail=exception.description,
    )

def json_body():
    if not request.is_json:
        return None, error("Request body phải là JSON", 415)
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return None, error("JSON body phải là một object", 400)
    return body, None

def user_public(user):
    """Thông tin hồ sơ không trả toàn bộ danh sách quan hệ trong mỗi bài viết."""
    return {"id": user["id"], "name": user["name"], "bio": user["bio"]}

@app.get("/users")
def list_users():
    query = request.args.get("name", "").strip().casefold()
    users = [user_public(user) for user in USERS
             if not query or query in user["name"].casefold()]
    return jsonify({"users": users}), 200

@app.post("/users")
def create_user():
    body, failure = json_body()
    if failure:
        return failure
    name = body.get("name", "").strip()
    if not name:
        raise ApiProblem(
            status=400, 
            title="Bad Request", 
            detail="name là bắt buộc", 
            type_path="missing-name")
    user = {"id": _next_ids["user"], "name": name,
            "bio": body.get("bio", "").strip(), "followers": [], "following": []}
    _next_ids["user"] += 1
    USERS.append(user)
    return jsonify(user_public(user)), 201

@app.get("/users/<int:user_id>")
def get_user(user_id):
    user = find_user(user_id)
    if user is None:
        raise ApiProblem(
            status=404, 
            title="Khong tim thay user", 
            type_path="user-not-found",
            resource_id=user_id,
            )
    return jsonify(user_public(user)), 200

@app.route("/users/<int:user_id>", methods=["PUT", "PATCH"])
def update_user(user_id):
    user = find_user(user_id)
    if user is None:
        return error("Không tìm thấy user", 404)
    body, failure = json_body()
    if failure:
        return failure
    if "name" in body:
        name = body["name"].strip() if isinstance(body["name"], str) else ""
        if not name:
            return error("name không được để trống", 400)
        user["name"] = name
    if "bio" in body:
        if not isinstance(body["bio"], str):
            return error("bio phải là chuỗi", 400)
        user["bio"] = body["bio"].strip()
    return jsonify(user_public(user)), 200

@app.delete("/users/<int:user_id>")
def delete_user(user_id):
    user = find_user(user_id)
    if user is None:
        return error("Không tìm thấy user", 404)
    USERS.remove(user)
    for other in USERS:
        other["followers"] = [uid for uid in other["followers"] if uid != user_id]
        other["following"] = [uid for uid in other["following"] if uid != user_id]
    removed_post_ids = {post["id"] for post in POSTS if post["user_id"] == user_id}
    POSTS[:] = [post for post in POSTS if post["user_id"] != user_id]
    COMMENTS[:] = [comment for comment in COMMENTS
                   if comment["user_id"] != user_id and comment["post_id"] not in removed_post_ids]
    return "", 204

@app.get("/users/<int:user_id>/profile")
def get_profile(user_id):
    user = find_user(user_id)
    if user is None:
        return error("Không tìm thấy user", 404)
    return jsonify({**user_public(user), "followers_count": len(user["followers"]),
                    "following_count": len(user["following"])}), 200

@app.put("/users/<int:user_id>/profile")
@app.patch("/users/<int:user_id>/profile")
def update_profile(user_id):
    return update_user(user_id)

@app.post("/users/<int:user_id>/following")
def follow_author(user_id):
    data = request.get_json(silent=True) or {}
    user2_id = data.get("user2_id")
    if not isinstance(user2_id, int):
        return error("user2_id hợp lệ là bắt buộc", 400)
    user, user2 = find_user(user_id), find_user(user2_id)
    if user is None or user2 is None:
        return error("Khong tim thay user hoac tac gia", 404)
    if user_id == user2_id:
        return error("Khong the tu theo doi chinh minh", 400)
    if user2_id not in user["following"]:
        user["following"].append(user2_id)
        user2["followers"].append(user_id)
    return jsonify({"message": "da theo doi thanh cong", "user2_id": user2_id}), 200

@app.delete("/users/<int:user_id>/following")
def unfollow_author(user_id):
    data = request.get_json(silent=True) or {}
    user2_id = data.get("user2_id")
    if not isinstance(user2_id, int):
        return error("user2_id la bat buoc", 400)
    user, user2 = find_user(user_id), find_user(user2_id)
    if user is None or user2 is None:
        return error("Khong tim thay user hoac tac gia", 404)
    if user2_id in user["following"]:
        user["following"].remove(user2_id)
        user2["followers"].remove(user_id)
    return "", 204

@app.get("/users/<int:user_id>/following")
def list_following(user_id):
    user = find_user(user_id)
    if user is None:
        return error("Khong tim thay user", 404)
    return jsonify({"users": [user_public(find_user(uid)) for uid in user["following"]]}), 200

@app.get("/users/<int:user_id>/followers")
def list_followers(user_id):
    user = find_user(user_id)
    if user is None:
        return error("Khong tim thay user", 404)
    return jsonify({"users": [user_public(find_user(uid)) for uid in user["followers"]]}), 200

def post_view(post):
    author = find_user(post["user_id"])
    return {**post, "author": user_public(author) if author else None,
            "comments_count": sum(c["post_id"] == post["id"] for c in COMMENTS)}

@app.get("/posts")
def list_posts():
    tag = request.args.get("tag", "").strip().casefold()
    author_id = request.args.get("author_id", type=int)
    posts = [post_view(post) for post in POSTS
             if (not tag or tag in post["tags"]) and
             (author_id is None or post["user_id"] == author_id)]
    return jsonify({"posts": posts}), 200

@app.post("/posts")
def create_post():
    body, failure = json_body()
    if failure:
        return failure
    return make_post(body)

def make_post(body):
    user_id = body.get("user_id")
    user = find_user(user_id) if isinstance(user_id, int) else None
    if user is None:
        return error("user_id hợp lệ là bắt buộc", 400)
    title = body.get("title", "").strip()
    content = body.get("content", "").strip()
    if not title or not content:
        return error("title và content là bắt buộc", 400)
    tags = body.get("tags", [])
    if not isinstance(tags, list) or any(not isinstance(tag, str) or not tag.strip() for tag in tags):
        return error("tags phải là danh sách chuỗi không rỗng", 400)
    post = {"id": _next_ids["post"], "user_id": user_id, "title": title,
            "content": content, "tags": sorted({tag.strip().casefold() for tag in tags}),
            "created_at": datetime.now().astimezone().isoformat()}
    _next_ids["post"] += 1
    POSTS.append(post)
    return jsonify(post_view(post)), 201

@app.get("/posts/<int:post_id>")
def get_post(post_id):
    post = find_post(post_id)
    if post is None:
        return error("Khong tim thay bai viet", 404)
    return jsonify(post_view(post)), 200

@app.route("/posts/<int:post_id>", methods=["PUT", "PATCH"])
def update_post(post_id):
    post = find_post(post_id)
    if post is None:
        return error("Khong tim thay bai viet", 404)
    body, failure = json_body()
    if failure:
        return failure
    for key in ("title", "content"):
        if key in body:
            value = body[key].strip() if isinstance(body[key], str) else ""
            if not value:
                return error(f"{key} không được để trống", 400)
            post[key] = value
    if "tags" in body:
        if not isinstance(body["tags"], list) or any(not isinstance(t, str) or not t.strip() for t in body["tags"]):
            return error("tags phải là danh sách chuỗi không rỗng", 400)
        post["tags"] = sorted({tag.strip().casefold() for tag in body["tags"]})
    return jsonify(post_view(post)), 200

@app.delete("/posts/<int:post_id>")
def delete_post(post_id):
    post = find_post(post_id)
    if post is None:
        return error("Khong tim thay bai viet", 404)
    POSTS.remove(post)
    COMMENTS[:] = [comment for comment in COMMENTS if comment["post_id"] != post_id]
    return "", 204

@app.get("/users/<int:user_id>/posts")
def list_user_posts(user_id):
    if find_user(user_id) is None:
        return error("Không tìm thấy user", 404)
    return jsonify({"posts": [post_view(post) for post in POSTS if post["user_id"] == user_id]}), 200

@app.post("/users/<int:user_id>/posts")
def create_user_post(user_id):
    body, failure = json_body()
    if failure:
        return failure
    if find_user(user_id) is None:
        return error("Không tìm thấy user", 404)
    body["user_id"] = user_id
    return make_post(body)

@app.get("/users/<int:user_id>/feed")
def user_feed(user_id):
    user = find_user(user_id)
    if user is None:
        return error("Không tìm thấy user", 404)
    followed = set(user["following"])
    return jsonify({"posts": [post_view(post) for post in reversed(POSTS)
                              if post["user_id"] in followed]}), 200

@app.get("/posts/<int:post_id>/comments")
def list_comments(post_id):
    if find_post(post_id) is None:
        return error("Không tìm thấy bài viết", 404)
    comments = [{**comment, "author": user_public(find_user(comment["user_id"]))}
                for comment in COMMENTS if comment["post_id"] == post_id]
    return jsonify({"comments": comments}), 200

@app.post("/posts/<int:post_id>/comments")
def create_comment(post_id):
    if find_post(post_id) is None:
        return error("Không tìm thấy bài viết", 404)
    body, failure = json_body()
    if failure:
        return failure
    user_id = body.get("user_id")
    content = body.get("content", "").strip()
    if not isinstance(user_id, int) or find_user(user_id) is None:
        return error("user_id hợp lệ là bắt buộc", 400)
    if not content:
        return error("content là bắt buộc", 400)
    comment = {"id": _next_ids["comment"], "post_id": post_id,
               "user_id": user_id, "content": content}
    _next_ids["comment"] += 1
    COMMENTS.append(comment)
    return jsonify({**comment, "author": user_public(find_user(user_id))}), 201

@app.route("/comments/<int:comment_id>", methods=["PUT", "PATCH"])
def update_comment(comment_id):
    comment = find_comment(comment_id)
    if comment is None:
        return error("Không tìm thấy bình luận", 404)
    body, failure = json_body()
    if failure:
        return failure
    content = body.get("content", "").strip()
    if not content:
        return error("content là bắt buộc", 400)
    comment["content"] = content
    return jsonify(comment), 200

@app.delete("/comments/<int:comment_id>")
def delete_comment(comment_id):
    comment = find_comment(comment_id)
    if comment is None:
        return error("Không tìm thấy bình luận", 404)
    COMMENTS.remove(comment)
    return "", 204

@app.get("/posts/<int:post_id>/tags")
def list_post_tags(post_id):
    post = find_post(post_id)
    if post is None:
        return error("Không tìm thấy bài viết", 404)
    return jsonify({"tags": post["tags"]}), 200

@app.post("/posts/<int:post_id>/tags")
def add_post_tag(post_id):
    post = find_post(post_id)
    if post is None:
        return error("Không tìm thấy bài viết", 404)
    body, failure = json_body()
    if failure:
        return failure
    tag = body.get("tag", "")
    if not isinstance(tag, str) or not tag.strip():
        return error("tag là bắt buộc", 400)
    tag = tag.strip().casefold()
    if tag not in post["tags"]:
        post["tags"].append(tag)
        post["tags"].sort()
    return jsonify({"post_id": post_id, "tags": post["tags"]}), 201

@app.delete("/posts/<int:post_id>/tags/<path:tag_name>")
def remove_post_tag(post_id, tag_name):
    post = find_post(post_id)
    if post is None:
        return error("Không tìm thấy bài viết", 404)
    tag = tag_name.strip().casefold()
    if tag not in post["tags"]:
        return error("Bài viết không có tag này", 404)
    post["tags"].remove(tag)
    return "", 204

@app.get("/tags/<path:tag_name>/posts")
def posts_by_tag(tag_name):
    tag = tag_name.strip().casefold()
    return jsonify({"posts": [post_view(post) for post in POSTS if tag in post["tags"]]}), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
