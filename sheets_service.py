import requests
import os
from datetime import date


class SheetHandler:
    def __init__(self, url):
        self.url = url

    # ── READ ── fetch all people from a sheet tab
    def get_people(self, sheet_name):
        payload = {
            "sheetName": sheet_name,
            "mode": "read"
        }
        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            return response.json()  # list of rows
        except Exception as e:
            print(f"Error reading sheet '{sheet_name}': {e}")
            return []

    # ── APPEND ── add a new student row [gender, name, grade]
    def add_student(self, sheet_name, name, gender, grade):
        payload = {
            "sheetName": sheet_name,
            "mode": "append",
            "name": name,
            "gender": gender,   # "B" or "G"
            "grade": grade      # e.g. "Pre-KG"
        }
        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error adding student '{name}': {e}")
            return f"Error: {e}"

    # ── APPEND ── add a new teacher row [name]
    def add_teacher(self, name):
        payload = {
            "sheetName": TEACHERS_TAB,
            "mode": "append",
            "name": name
        }
        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error adding teacher '{name}': {e}")
            return f"Error: {e}"

    # ── NEW ── mark attendance for today (list of "Att" or "" per person)
    def mark_attendance(self, sheet_name, attendance_values, attendance_date=None):
        if attendance_date is None:
            attendance_date = date.today().strftime("%d/%m/%Y")  # e.g. "13/04/2025"

        payload = {
            "sheetName": sheet_name,
            "mode": "new",
            "date": attendance_date,
            "values": attendance_values  # e.g. ["Att", "", "Att", "Att"]
        }
        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error marking attendance for '{sheet_name}': {e}")
            return f"Error: {e}"


# Class names matching your Google Sheet tab names exactly
CLASSES = [
    "Pre-KG",
    "KG",
    "1-2",
    "3-4",
    "5-6",
    "الخدام + ال helpers"
]

TEACHERS_TAB = "الخدام + ال helpers"