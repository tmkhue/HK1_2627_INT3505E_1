from flask import Flask, jsonify, request
from uuid import uuid4
app = Flask(__name__)
STUDENT = [
    {"id": 1, "name": "Tran Minh A", "gpa": 4.0, "year": 1},
    {"id": 2, "name": "Nguyen Van B", "gpa": 3.2, "year": 3},
    {"id": 3, "name": "Le Minh C", "gpa": 2.8, "year": 2},
    {"id": 4, "name": "Pham Van D", "gpa": 3.8, "year": 4},
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

    gpa = body.get("gpa")
    if gpa is None:
        gpa = 0
    if not isinstance(gpa, (float, int)):
        return {"error": "GPA phai la so"}, 400
    if not (0<=gpa<=4.0):
        return {"error": "GPA khong hop le"}, 400

    year = body.get("year")
    if year is None:
        year = 1
    if not isinstance(year, int) or isinstance(year, bool):
        return jsonify({"error": "Nam hoc phai la so"}), 400
    if not (1<=year<=4):
        return jsonify({"error": "Nam hoc khong hop le"}), 400
    
    student = {
        "id": len(STUDENT) + 1,
        "name": name,
        "gpa": gpa,
        "year": year
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
def students_select():
    min_gpa = request.args.get("gpa", type=float)
    student_name = request.args.get("name", "").strip().lower()
    school_year = request.args.get("year", type=int)

    res = STUDENT

    if min_gpa is not None:
        res = [s for s in res if s.get("gpa", 0.0) >= min_gpa]
    if student_name:
        res = [s for s in res if student_name in s.get("name", "").lower()]
    if school_year is not None:
        res = [s for s in res if s.get("year", 0) == school_year]
    return jsonify({"students": res}), 200

@app.route("/students/<int:student_id>", methods=["DELETE"])
def remove_student(student_id):
    student = STUDENT[student_id-1]
    if student is None:
        return jsonify({"error": "Khong tim thay"}), 404
    if student["gpa"] > 1:
        return jsonify({"error": "Khong the xoa sinh vien"}), 409
    STUDENT.pop(student_id-1)
    return"", 204
    
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)