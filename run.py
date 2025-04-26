import sys # Used to terminate the execution of the Python script.
import gspread # Tools to easily work with the content of Google Sheets
from google.oauth2.service_account import Credentials # Credentials class to handle the authentication

# Google Sheets API scope
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]
# Load credentials and authorize with error handling
try:
    CREDS = Credentials.from_service_account_file('creds.json')
    SCOPED_CREDS = CREDS.with_scopes(SCOPE) # scope the Google APIs script needs access to
    GSPREAD_CLIENT = gspread.authorize(SCOPED_CREDS) # authenticated client object
    SHEET = GSPREAD_CLIENT.open('forever_home_friends') # open the Google Sheet
except FileNotFoundError:
    print("Error: File 'creds.json' not found.")
    print("Make sure the 'creds.json' file exists in the project directory.")
    sys.exit(1)
except gspread.exceptions.SpreadsheetNotFound:
    print("Error: Google Sheet 'forever_home_friends' not found.")
    print("Make sure the the sheet exists and the service account has access.")
    sys.exit(1)
except Exception as e:
    print(f"Error: An unexpected error occurred: {e}")
    sys.exit(1)

# Access individual worksheets with error handling
try:
    children_sheet = SHEET.worksheet("Children")
    pets_sheet = SHEET.worksheet("Pets")
    owners_sheet = SHEET.worksheet("Owners")
    print("Success: Successfully connected to Worksheets.")
except gspread.exceptions.WorksheetNotFound as e:
    print(f"Error: Worksheet not found - {e}")
    print("Make sure 'Children', 'Pets', and 'Owners' worksheets exist.")
    sys.exit(1)
except Exception as e:
    print(f"Error: An unexpected error occurred accessing worksheets: {e}")
    sys.exit(1)

# Helper Functions Section

def get_next_id(worksheet):
    """
    Returns the next consecutive ID for a new entry.
    Assumes that the IDs are in the first column.
    Returns ID 1 if the sheet is empty (except header).
    """
    # Get all data from the specified worksheet
    try:
        all_values = worksheet.get_all_values()
        # If the sheet has more than one row (header + data),
        # take all rows starting from the second row (index 1).
        # Otherwise (if only 0 or 1 row), create an empty list for data_rows.
        data_rows = all_values[1:] if len(all_values) > 1 else []
        if not data_rows:
            return 1 # If there's no data, the first ID is set to 1.
        # Find the highest existing ID
        # Initialize a variable to store the maximum ID found.
        max_id = 0
        for row in data_rows:
            # Check if row exists and first cell is digit to avoid errors.
            if row and row[0].isdigit():
                # Convert ID to integer, update max_id if the current row ID is greater than current max_id.
                max_id = max(max_id, int(row[0]))
        # Calculate and return the next ID
        return max_id + 1
    # If any error occurs during the 'try' block, print a warning message with error details. 
    except Exception as e:
        print(f"Warning: Error retrieving next ID: {e}")
        # Return None if failed to get an ID for calling functions (like add_child and add_pet).
        return None
    
def validate_input(prompt, validation_func, error_message, **kwargs):
    """
    Generic function to validate user input.
        prompt (str): Message displayed to user.
        validation_func (callable): Function to validate the input (True if valid).
        error_message (str): Message displayed on invalid input.
        **kwargs: Additional arguments to pass.
    Returns:
        str: Validated user input.
    """
    while True: # start an infinite loop that break when on valid input
        user_input = input(prompt).strip() # removes any leading/trailing spaces.
        if not user_input: # print a warning for empty input.
            print("Warning: Input cannot be empty. Please try again.") 
            continue  # skips the rest of the loop and asks for input again.
        if validation_func(user_input, **kwargs): # if validation_func returns True, return the valid user input.
            return user_input
        else: # If validation_func returns False, print the specific 'error_message'.
            print(error_message)

def validate_integer(input_str):
    """Checks if the input string is a valid integer."""
    return input_str.isdigit()  # check if all characters are digits to ensure the user entered a number (like add ID).

def validate_range(input_str, min_val, max_val):
    """Checks if input is an integer within a specified range."""
    if not input_str.isdigit(): # check if all characters are digits.
        return False
    value = int(input_str) # convert the input string to integer number
    return min_val <= value <= max_val # check if that number falls within the specified inclusive range (like add age).

def validate_pet_type(input_str):
    """Checks if the input is 'puppy' or 'kitty'."""
    return input_str.lower() in ["puppy", "kitty"] # convert input to lowercase, check if string is present in the predefined list (like add pet, case-insensitive). 

# Placeholder for application logic
if __name__ == "__main__": # checks if the script is being run directly.
    print("Application start.")
    # Main loop will go here
    print("Application finish.")