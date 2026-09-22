"""
REST API service
-----------------
A small in-memory REST API for "students". No database is used on purpose,
so the lab stays simple: data resets every time this container restarts.
This is intentional and a good discussion point for a distributed systems
class: what happens to state when a container dies? (Answer: it's gone,
unless you use a volume or an external database - see Part 7.)
"""

import socket

from flask import Flask, jsonify, request

app = Flask(__name__)

students = [
    {"id": 1, "name": "Ayu Lestari", "course": "Distributed Systems"},
    {"id": 2, "name": "Budi Santoso", "course": "Distributed Systems"},
    {"id": 3, "name": "Citra Dewi", "course": "Distributed Systems"},
]
next_id = 4


@app.route("/api/health", methods=["GET"])
def health():
    """Simple endpoint to check the API is alive and which container answered."""
    return jsonify({"status": "ok", "hostname": socket.gethostname()})


@app.route("/api/students", methods=["GET"])
def get_students():
    return jsonify(students)


@app.route("/api/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    student = next((s for s in students if s["id"] == student_id), None)
    if student is None:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(student)


@app.route("/api/students", methods=["POST"])
def add_student():
    global next_id
    data = request.get_json(silent=True) or {}
    if "name" not in data:
        return jsonify({"error": "field 'name' is required"}), 400

    new_student = {
        "id": next_id,
        "name": data["name"],
        "course": data.get("course", "Distributed Systems"),
    }
    students.append(new_student)
    next_id += 1
    return jsonify(new_student), 201


@app.route("/api/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    student = next((s for s in students if s["id"] == student_id), None)
    if student is None:
        return jsonify({"error": "Student not found"}), 404

    data = request.get_json(silent=True) or {}
    student["name"] = data.get("name", student["name"])
    student["course"] = data.get("course", student["course"])
    return jsonify(student)


@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    global students
    student = next((s for s in students if s["id"] == student_id), None)
    if student is None:
        return jsonify({"error": "Student not found"}), 404

    students = [s for s in students if s["id"] != student_id]
    return jsonify({"message": "deleted"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
