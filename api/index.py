@app.route("/class/<path:class_name>")
def class_page(class_name):
    class_name = unquote(class_name)
    if class_name not in CLASSES:
        return "Class not found", 404

    people = sheets.get_people(class_name)

    print(f"DEBUG class_page: {class_name}")
    last = sheets.get_last_attendance(class_name)
    print(f"DEBUG last: {last}")

    this_week = False
    existing_date = None
    existing_values = []

    if last and last.get("date"):
        print(f"DEBUG date found: {last['date']}")
        result = is_same_week(last["date"])
        print(f"DEBUG is_same_week: {result}")
        if result:
            this_week = True
            existing_date = last["date"]
            existing_values = last.get("values", [])

    print(f"DEBUG this_week: {this_week}")

    return render_template(
        "class.html",
        class_name=class_name,
        people=people,
        this_week=this_week,
        existing_date=existing_date,
        existing_values=existing_values
    )