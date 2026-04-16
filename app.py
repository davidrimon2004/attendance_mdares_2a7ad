from flask import Flask, render_template, request, jsonify
import os
from sheets_service import SheetHandler, CLASSES

app = Flask(__name__)

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
    # people = list of rows:
    #   students → [B/G, Name, Grade]
    #   teachers → [Name]
    return render_template("class.html", class_name=class_name, people=people)


@app.route("/submit-attendance", methods=["POST"])
def submit_attendance():
    data = request.get_json()
    class_name = data.get("class_name")
    attendance = data.get("attendance")

    print("=== SUBMIT ATTENDANCE ===")
    print("class_name:", class_name)
    print("attendance:", attendance)

    result = sheets.mark_attendance(class_name, attendance)
    
    print("result from sheets:", result)
    
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
    gender = data.get("gender")  # "B" or "G"
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


# ─────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
