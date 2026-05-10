import sys
import os
from urllib.parse import unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from flask import Flask, render_template, request, jsonify
from sheets_service import SheetHandler, CLASSES, is_same_week

TEMPLATES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Templates")
app = Flask(__name__, template_folder=TEMPLATES)

sheets = SheetHandler(os.getenv("url"))


@app.route("/")
def index():
    return render_template("index.html", classes=CLASSES)


@app.route("/class/<path:class_name>")
def class_page(class_name):
    class_name = unquote(class_name)
    if class_name not in CLASSES:
        return "Class not found", 404

    people = sheets.get_people(class_name)

    # Check if attendance was already recorded this week
    last = sheets.get_last_attendance(class_name)
    this_week = False
    existing_date = None
    existing_values = []

    if last and last.get("date"):
        if is_same_week(last["date"]):
            this_week = True
            existing_date = last["date"]
            existing_values = last.get("values", [])

    return render_template(
        "class.html",
        class_name=class_name,
        people=people,
        this_week=this_week,
        existing_date=existing_date,
        existing_values=existing_values
    )


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


@app.route("/update-attendance", methods=["POST"])
def update_attendance():
    data = request.get_json()
    class_name = data.get("class_name")
    attendance_date = data.get("date")
    attendance = data.get("attendance")
    if not class_name or not attendance_date or attendance is None:
        return jsonify({"error": "Missing data"}), 400
    if class_name not in CLASSES:
        return jsonify({"error": "Invalid class"}), 400
    result = sheets.update_attendance(class_name, attendance_date, attendance)
    return jsonify({"message": result})


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