import re
from dateutil import parser as dp
from datetime import date, timedelta

date_str = "Sun May 10 2026 00:00:00 GMT+0300 (توقيت شرق أوروبا الصيفي)"
cleaned = re.sub(r'\(.*?\)', '', str(date_str)).strip()
print("Cleaned:", cleaned)
recorded = dp.parse(cleaned).date()
today = date.today()
days_since_friday = (today.weekday() - 4) % 7
last_fri = today - timedelta(days=days_since_friday)
print("Recorded:", recorded)
print("Last Friday:", last_fri)
print("Is same week:", recorded >= last_fri)