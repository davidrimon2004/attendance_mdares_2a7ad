import os
import json
import base64
from datetime import date, datetime, timedelta
from dateutil import parser as dateparser
import re

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

CLASSES = [
    "Pre-KG",
    "KG",
    "1-2",
    "3-4",
    "5-6",
    "الخدام + ال helpers"
]

TEACHERS_TAB = "الخدام + ال helpers"


def get_sheets_service():
    creds_json = json.loads(base64.b64decode(os.getenv("GOOGLE_CREDS")))
    creds = Credentials.from_service_account_info(creds_json, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)
    return service.spreadsheets()


class SheetHandler:
    def __init__(self, spreadsheet_id):
        self.spreadsheet_id = spreadsheet_id
        self._sheet = None  # lazy — don't connect at startup

    @property
    def sheet(self):
        if self._sheet is None:
            self._sheet = get_sheets_service()
        return self._sheet

    def get_class_data(self, sheet_name):
        """Fetch all data from the sheet in one API call."""
        try:
            result = self.sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!A1:ZZ"
            ).execute()
            rows = result.get("values", [])

            if len(rows) <= 1:
                return [], {"date": None, "values": []}

            is_teacher = sheet_name == TEACHERS_TAB
            data_cols = 1 if is_teacher else 3

            header_row = rows[0]
            data_rows = rows[1:]

            # Extract people
            people = []
            for row in data_rows:
                person = row[:data_cols]
                while len(person) < data_cols:
                    person.append("")
                people.append(person)

            # Extract the attendance column to display.
            # Prefer the latest date from the current Friday-through-Thursday week,
            # otherwise fall back to the latest valid date.
            date_val = None
            values = []
            if len(header_row) > data_cols:
                last_col_index = None
                latest_date = None
                current_week_col_index = None
                current_week_date = None
                current_week_dt = None

                for col_index in range(data_cols, len(header_row)):
                    dt = parse_sheet_date(header_row[col_index])
                    if dt is None:
                        continue
                    if latest_date is None or dt > latest_date:
                        latest_date = dt
                        last_col_index = col_index
                    if is_same_week(header_row[col_index]):
                        if current_week_dt is None or dt > current_week_dt:
                            current_week_dt = dt
                            current_week_col_index = col_index
                            current_week_date = header_row[col_index]

                if current_week_col_index is not None:
                    date_val = current_week_date
                    last_col_index = current_week_col_index
                elif last_col_index is not None:
                    date_val = header_row[last_col_index]

                if last_col_index is not None:
                    for row in data_rows:
                        values.append(row[last_col_index] if last_col_index < len(row) else "")

            return people, {"date": date_val, "values": values}

        except Exception as e:
            print(f"Error reading class data for '{sheet_name}': {e}")
            return [], {"date": None, "values": []}

    def add_student(self, sheet_name, name, gender, grade):
        try:
            self.sheet.values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!A:C",
                valueInputOption="RAW",
                body={"values": [[name, gender, grade]]}
            ).execute()
            return f"Added {name}"
        except Exception as e:
            print(f"Error adding student '{name}': {e}")
            return f"Error: {e}"

    def add_teacher(self, name):
        try:
            self.sheet.values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{TEACHERS_TAB}'!A:A",
                valueInputOption="RAW",
                body={"values": [[name]]}
            ).execute()
            return f"Added {name}"
        except Exception as e:
            print(f"Error adding teacher '{name}': {e}")
            return f"Error: {e}"

    def mark_attendance(self, sheet_name, attendance_values, attendance_date=None):
        if attendance_date is None:
            attendance_date = date.today().strftime("%d/%m/%y")
        try:
            result = self.sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!1:1"
            ).execute()
            header = result.get("values", [[]])[0]

            target_col = None
            target_date = None
            target_dt = None
            for i, h in enumerate(header):
                dt = parse_sheet_date(h)
                if dt is None:
                    continue
                if is_same_week(h):
                    if target_dt is None or dt > target_dt:
                        target_dt = dt
                        target_col = i + 1
                        target_date = h

            if target_col is None:
                next_col = len(header) + 1
                col_letter = col_num_to_letter(next_col)

                self.sheet.values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"'{sheet_name}'!{col_letter}1",
                    valueInputOption="RAW",
                    body={"values": [[attendance_date]]}
                ).execute()

                self.sheet.values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"'{sheet_name}'!{col_letter}2",
                    valueInputOption="RAW",
                    body={"values": [[v] for v in attendance_values]}
                ).execute()

                return f"Attendance marked for {attendance_date}"

            col_letter = col_num_to_letter(target_col)
            self.sheet.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!{col_letter}2",
                valueInputOption="RAW",
                body={"values": [[v] for v in attendance_values]}
            ).execute()

            return f"Updated attendance for {target_date}"
        except Exception as e:
            print(f"Error marking attendance for '{sheet_name}': {e}")
            return f"Error: {e}"

    def update_attendance(self, sheet_name, attendance_date, attendance_values):
        try:
            result = self.sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!1:1"
            ).execute()
            headers = result.get("values", [[]])[0]

            target_col = None
            for i, h in enumerate(headers):
                if str(h) == str(attendance_date):
                    target_col = i + 1
                    break

            if target_col is None:
                return f"Error: Date column not found: {attendance_date}"

            col_letter = col_num_to_letter(target_col)
            self.sheet.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!{col_letter}2",
                valueInputOption="RAW",
                body={"values": [[v] for v in attendance_values]}
            ).execute()

            return f"Updated attendance for {attendance_date}"
        except Exception as e:
            print(f"Error updating attendance for '{sheet_name}': {e}")
            return f"Error: {e}"


def col_num_to_letter(n):
    """Convert column number to letter (1=A, 26=Z, 27=AA, etc.)"""
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result


def parse_sheet_date(date_str):
    try:
        cleaned = re.sub(r'\(.*?\)', '', str(date_str)).strip()
        if not cleaned:
            return None
        try:
            return datetime.strptime(cleaned, "%d/%m/%y").date()
        except ValueError:
            return dateparser.parse(cleaned, dayfirst=True).date()
    except Exception:
        return None


def current_week_friday(today=None):
    """Return the most recent Friday on or before the given date (or today)."""
    if today is None:
        today = date.today()
    days_since_friday = (today.weekday() - 4) % 7  # 0 if today is Friday
    return today - timedelta(days=days_since_friday)


def is_same_week(date_str, today=None):
    """Return True if date_str falls in the current week from Friday through Thursday."""
    recorded = parse_sheet_date(date_str)
    if recorded is None:
        return False
    start = current_week_friday(today)
    end = start + timedelta(days=7)
    return start <= recorded < end