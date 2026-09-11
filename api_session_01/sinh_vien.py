from flask import Flask, jsonify, request
from uuid import uuid4
app = Flask(__name__)
STUDENT = [
    {"id": "1", "name": "Tran Minh A", "gpa": 4.0},
    {"id": "2", "name": "Nguyen Van B", "gpa": 3.2},
    {"id": "3", "name": "Le Minh C", "gpa": 2.8},
    {"id": "4", "name": "Pham Van D", "gpa": 3.8},
]

def find_by_id(student_id):
    for s in STUDENT:
        if str(s["id"]) == str(student_id):
            return s
    return None

@app.route("/students", methods=["POST"])
def create_student():
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    if not name:
        return jsonify({"error": "hay nhap name"}), 400
    student = {
        "id": str(uuid4()),
        "name": name,
        "gpa": body.get("gpa", 0.0),
    }
    STUDENT.append(student)
    return jsonify(student), 201

@app.route("/students/<student_id>", methods=["GET"])
def get_student(student_id):
    student = find_by_id(student_id)
    if student is None:
        return jsonify({"error": "Khong tim thay"}), 404
    return jsonify(student), 200

@app.route("/students", methods=["GET"])
def students_by_name():
    min_gpa = request.args.get("gpa", type=float)
    student_name = request.args.get("name", "").strip().lower()

    res = STUDENT

    if min_gpa is not None:
        res = [s for s in res if s.get("gpa", 0.0) >= min_gpa]
    if student_name:
        res = [s for s in res if student_name in s.get("name", "").lower()]
    return jsonify({"students": res}), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)