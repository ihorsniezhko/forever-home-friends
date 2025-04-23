import sys # Used to terminate the execution of the Python script.
import gspread # Tools to easily work with the content of Google Sheets
from google.oauth2.service_account import Credentials # Credentials class to handle the authentication

# Google Sheets API scope
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]
