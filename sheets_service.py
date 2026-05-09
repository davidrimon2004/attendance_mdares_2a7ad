import requests
import os
from datetime import date, datetime, timedelta


class SheetHandler:
    def __init__(self, url):
        self.url = url

    # ── READ ── fetch all people from a sheet tab
    def get_people(self, sheet_name):
        payload = {"sheetName": sheet_name, "mode": "read"}
        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error reading sheet '{sheet_name}': {e}")
            return []

    # ── LASTDATE ── get the last recorded attendance date + values
    def get_last_attendance(self, sheet_name):
        payload = {"sheetName": sheet_name, "mode": "lastdate"}
        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            return response.json()  # { "date": "dd/mm/yy", "values": ["Att", "", ...] }
        except Exception as e:
            print(f"Error getting last date for '{sheet_name}': {e}")
            return None

    # ── APPEND ── add a new student row
    def add_student(self, sheet_name, name, gender, grade):
        payload = {
            "sheetName": sheet_name,
            "mode": "append",
            "name": name,
            "gender": gender,
            "grade": grade
        }
        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error adding student '{name}': {e}")
            return f"Error: {e}"

    # ── APPEND ── add a new teacher row
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

    # ── NEW ── submit fresh attendance for today
    def mark_attendance(self, sheet_name, attendance_values, attendance_date=None):
        if attendance_date is None:
            attendance_date = date.today().strftime("%d/%m/%y")
        payload = {
            "sheetName": sheet_name,
            "mode": "new",
            "date": attendance_date,
            "values": attendance_values
        }
        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error marking attendance for '{sheet_name}': {e}")
            return f"Error: {e}"

    # ── UPDATE ── overwrite attendance for an existing date column
    def update_attendance(self, sheet_name, attendance_date, attendance_values):
        payload = {
            "sheetName": sheet_name,
            "mode": "update",
            "date": attendance_date,
            "values": attendance_values
        }
        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error updating attendance for '{sheet_name}': {e}")
            return f"Error: {e}"


def last_friday(from_date=None):
    """Return the most recent Friday on or before from_date."""
    if from_date is None:
        from_date = date.today()
    # weekday(): Monday=0 ... Friday=4 ... Sunday=6
    days_since_friday = (from_date.weekday() - 4) % 7
    return from_date - timedelta(days=days_since_friday)


def is_same_week(date_str):
    """
    Return True if date_str (dd/mm/yy) falls in the current
    Friday-to-Thursday week (i.e. >= last Friday).
    """
    try:
        recorded = datetime.strptime(date_str, "%d/%m/%y").date()
        return recorded >= last_friday()
    except Exception:
        return False


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