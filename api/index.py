import sys
import os

# Allow imports from the root folder (sheets_service.py)
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, request, jsonify
from sheets_service import SheetHandler, CLASSES

app = Flask(__name__, template_folder="templates")

# Load the Google Apps Script URL from environment variable
sheets = SheetHandler(os.getenv("url"))


# ─────────────────────────────────────────────
# HOME — pick a class from dropdown
# ─────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html", classes=CLASSES)


# ─────────────────────────────────────────────
# CLASS PAGE — mark attendance for a class
# ─────────────────────────────────────────────
@app.route("/class/<class_name>")
def class_page(class_name):
    if class_name not in CLASSES:
        return "Class not found", 404

    people = sheets.get_people(class_name)
    return render_template("class.html", class_name=class_name, people=people)


@app.route("/submit-attendance", methods=["POST"])
def submit_attendance():
    data = request.get_json()
    class_name = data.get("class_name")
    attendance = data.get("attendance")

    if not class_name or attendance is None:
        return jsonify({"error": "Missing data"}), 400

    if class_name not in CLASSES:
        return jsonify({"error": "Invalid class"}), 400

    result = sheets.mark_attendance(class_name, attendance)
    return jsonify({"message": result})


# ─────────────────────────────────────────────
# MANAGE PAGE — add/remove students & teachers
# ─────────────────────────────────────────────
@app.route("/manage")
def manage():
    return render_template("manage.html", classes=CLASSES)


@app.route("/add-student", methods=["POST"])
def add_student():
    data = request.get_json()
    class_name = data.get("class_name")
    name = data.get("name")
    gender = data.get("gender")
    grade = data.get("grade")

    if not all([class_name, name, gender, grade]):
        return jsonify({"error": "Missing fields"}), 400

    if class_name not in CLASSES:
        return jsonify({"error": "Invalid class"}), 400

    result = sheets.add_student(class_name, name, gender, grade)
    return jsonify({"message": result})


@app.route("/add-teacher", methods=["POST"])
def add_teacher():
    data = request.get_json()
    name = data.get("name")

    if not name:
        return jsonify({"error": "Missing name"}), 400

    result = sheets.add_teacher(name)
    return jsonify({"message": result})
