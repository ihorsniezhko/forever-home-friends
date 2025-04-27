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

def confirm_action(prompt):
    """Asks user for Yes/No confirmation."""
    while True:
        choice = input(f"{prompt} (Yes/No): ").strip().lower() # ask user a question and only accept "yes" or "no" as valid answers.
        if choice == "yes":
            return True
        elif choice == "no":
            return False
        else:
            print("Warning: Please enter 'Yes' or 'No'.")

def find_row_by_id(worksheet, id_str):
    """
    Finds a row in a worksheet by ID (first column).
        worksheet: The gspread worksheet object.
        id_str: The ID as a string to search for.

    Returns:
        tuple: (row_data, row_index) if found, otherwise (None, None).
               Returns (None, -1) if an error occurs during sheet access.
    """
    if not id_str.isdigit(): # сheck if provided 'id_str' actually contains only digits.
        return None, None # input format is wrong.

    try: # attempt Sheet access
        all_values = worksheet.get_all_values() # fetch all rows and columns from specified worksheet.
        for index, row in enumerate(all_values): # provides index of the row and row data.
            if row and row[0] == id_str: # compare value in the first cell (row[0]) with 'id_str'.
                return row, index + 1 # return a tuple: list of data for matching row and row number.  
        return None, None # no row with the specified ID was found.
    except gspread.exceptions.APIError as e:
        print(f"Error: Google Sheets API Error: {e}") # if error related to the Google Sheets API
        print("   Please check your connection and permissions.")
        return None, -1 # -1 indicate that error occurred during the search, not that the row wasn't found (returns None, None).
    except Exception as e: # catch other unexpected errors during 'try'.
        print(f"Warning: An unexpected error occurred finding row by ID: {e}")
        return None, -1 

def find_row_by_child_name(worksheet, full_name):
    """
    Finds a row in the Owners worksheet by child's full name.
        worksheet: Owners gspread worksheet object.
        full_name (str): Child's full name to search for.

    Returns:
        tuple: (row_data, row_index) if found, otherwise (None, None).
               Returns (None, -1) if an error occurs during sheet access.
    """
    try:
        all_values = worksheet.get_all_values() # fetch all rows and columns from specified worksheet.
        for index, row in enumerate(all_values): # provides index of the row and row data.
            if row and len(row) > 0 and row[0] == full_name:  # check if row has at least one column, compare the value in the first cell with the 'full_name' string. 
                return row, index + 1 # return a tuple: list of data for matching row (Child Name, Pet ID). 
        return None, None # no row with the specified child's name was found.
    except gspread.exceptions.APIError as e:
        print(f"Error: Google Sheets API Error: {e}")
        print("   Please check your connection and permissions.")
        return None, -1 # -1 indicate that error occurred during the search, not that the name wasn't found (returns None, None).
    except Exception as e: # catch other unexpected errors during 'try'.
        print(f"Warning: An unexpected error occurred finding row by name: {e}")
        return None, -1

def find_row_by_pet_id(worksheet, pet_id_str):
    """
    Finds a row in the Owners worksheet by Pet ID (second column).
        worksheet: The Owners gspread worksheet object.
        pet_id_str (str): The pet ID as a string to search for.

    Returns:
        tuple: (row_data, row_index) if found, otherwise (None, None).
               Returns (None, -1) if an error occurs during sheet access.
    """
    if not pet_id_str.isdigit(): # сheck if provided 'pet_id_str' actually contains only digits.
        return None, None # # input format is wrong.

    try:
        all_values = worksheet.get_all_values() # fetch all rows and columns from specified worksheet.
        for index, row in enumerate(all_values): # provides index of the row and row data.
            if row and len(row) > 1 and row[1] == pet_id_str: # check if row has at least two columns, compare the value in the second cell with the 'pet_id_str' string.
                return row, index + 1 # return a tuple: list of data for matching row (Child Name, Pet ID). 
        return None, None # no row with the specified Pet ID was found.
    except gspread.exceptions.APIError as e:
        print(f"Error: Google Sheets API Error: {e}")
        print("   Please check your connection and permissions.")
        return None, -1 # -1 indicate that error occurred during the search, not that the ID wasn't found (returns None, None).
    except Exception as e: # catch other unexpected errors during 'try'.
        print(f"Warning: An unexpected error occurred finding row by pet ID: {e}")
        return None, -1

# Core Functions Section (Menu Options)

def add_child():
    """Adds a new child record to the 'Children' sheet."""
    print("\n- Add New Child -")
    first_name = input("Enter Child's First Name: ").strip().capitalize() # ask for the first name, remove extra whitespace, make first letter uppercase.
    if not first_name: # if empty, print a warning and exit.
        print("Warning: First name cannot be empty.")
        return

    last_name = input("Enter Child's Last Name: ").strip().capitalize() # ask for the last name, remove extra whitespace, make first letter uppercase.
    if not last_name: # if empty, print a warning and exit.
        print("Warning: Last name cannot be empty.")
        return
    
    # Get and Validate Age (valid number string between 5 and 18).
    age_str = validate_input(
        "Enter Child's Age (5-18 years): ",  # call validate_input helper function, pass the prompt to display to user. 
        lambda x: validate_range(x, min_val=5, max_val=18),  # pass validation function using anonymous 'lambda' that calls 'validate_range' ensuring 'x' between 5 and 18.
        "Warning: Invalid age. Please enter a number between 5 and 18."
    )

    # Get the Next Available ID
    next_id = get_next_id(children_sheet) # call the get_next_id helper function
    if next_id is None:  # check if returned None, indicates error trying to get the ID.
        print("Error: Could not determine next ID. Aborting.")
        return
    # Prepare the New Row Data
    new_child_data = [next_id, first_name, last_name, int(age_str)] # convert age string to an integer and create a list containing data for the new row.
    # Try to Append Data to Google Sheet
    try: # 'try' block as access to Google Sheets can fail.
        children_sheet.append_row(new_child_data) # 'append_row' method to add 'new_child_data' list as a new bottom row.
        print("-" * 10)
        print(f"Success: Child '{first_name} {last_name}' added successfully!") # if append is ok, show a confirmation message
        print(f"   Assigned ID: {next_id}")
        print("-" * 10)
    # Handle Errors During Append
    except gspread.exceptions.APIError as e: # specific errors related to Google Sheets API.
        print(f"Error: Google Sheets API Error adding child: {e}")
        print("   Please check your connection and permissions.")
    except Exception as e: # any unexpected errors during the append.
        print(f"Error: An unexpected error occurred adding child: {e}")



# Placeholder for application logic
if __name__ == "__main__": # checks if the script is being run directly.
    print("Application start.")
    # Main loop will go here
    print("Application finish.")