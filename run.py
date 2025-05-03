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

def confirm_action(prompt):
    """Asks for Yes/No confirmation (accepts y/n)."""
    while True:
        choice = input(f"{prompt} (y/n): ").strip().lower() # ask user a question and only accept "y" or "n" as valid answers.
        if choice == "y":
            return True
        elif choice == "n":
            return False
        else:
            print("Warning: Please enter 'y' or 'n'.")

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
    
    # Get and Validate Age (valid number string between 5 and 18 years).
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
    except gspread.exceptions.APIError as e: # specific errors related to Google Sheets API.
        print(f"Error: Google Sheets API Error adding child: {e}")
        print("   Check your connection and permissions.")
    except Exception as e: # any unexpected errors during the append.
        print(f"Error: An unexpected error occurred adding child: {e}")

def add_pet():
    """Adds a new pet record to the 'Pets' sheet."""
    print("\n- Add New Pet -")
    nickname = input("Enter Pet's Nickname: ").strip().capitalize() # ask for the  Pet's Nickname, remove extra whitespace, make first letter uppercase.
    if not nickname: # if empty, print a warning and exit.
        print("Warning: Nickname cannot be empty.")
        return
    
    # Get and Validate Age (valid number string between 0 and 12 months).
    age_str = validate_input(
        "Enter Pet's Age (0-12 months): ", # call validate_input helper function, pass the prompt to display to user. 
        lambda x: validate_range(x, min_val=0, max_val=12), # pass validation function using anonymous 'lambda' that calls 'validate_range' ensuring 'x' between 0 and 12.
        "Warning: Invalid age. Please enter a number between 0 and 12."
    )
    # Get and Validate Pet Type
    pet_type_short = validate_input(
        "Enter Pet Type (p for puppy / k for kitty): ", # call validate_input helper function, pass the prompt to display to user.
        lambda x: x.lower() in ['p', 'k'], # lambda function to ensure the validated input is lowercse ('p' or 'k').
        "Warning: Invalid type. Please enter 'p' or 'k'."
    ).lower() # ensure that final value is always lowercase.

    # Convert 'p' / 'k' to 'puppy' / 'kitty'for storage
    if pet_type_short == 'p':
        pet_type = 'puppy'
    elif pet_type_short == 'k':
        pet_type = 'kitty'
    else:
        print("Error: Unexpected error processing pet type. Aborting.") # fallback in case of error.
        return

    # Get the Next Available ID
    next_id = get_next_id(pets_sheet) # call the get_next_id helper function
    if next_id is None: # check if returned None, indicates error trying to get the ID.
        print("Error: Could not determine next ID. Aborting.")
        return

    new_pet_data = [next_id, nickname, int(age_str), pet_type] # convert age string to an integer and create a list containing data for the new row.

    # Try to Append Data to Google Sheet
    try: # 'try' block as access to Google Sheets can fail.
        pets_sheet.append_row(new_pet_data) # 'append_row' method to add 'new_pet_data' list as a new bottom row.
        print("-" * 10)
        print(f"Success: Pet '{nickname}' ({pet_type}) added successfully!") # if append is ok, show a confirmation message
        print(f"   Assigned ID: {next_id}")
        print("-" * 10)
    except gspread.exceptions.APIError as e: # specific errors related to Google Sheets API.
        print(f"Error: Google Sheets API Error adding pet: {e}")
        print("   Check your connection and permissions.")
    except Exception as e: # any unexpected errors during the append.
        print(f"Error: An unexpected error occurred adding pet: {e}")

def link_child_pet():
    """Links a child to a pet in the 'Owners' sheet."""
    print("\n- Link Child and Pet -")

    # Get and Validate Child ID
    while True:
        child_id_str = validate_input(
            "Enter ID of the Child: ", # call validate_input helper function, pass the prompt to display to user.
            validate_integer, # pass validate_integer function
            "Warning: Invalid ID. Please enter the child's ID number."
        )
        child_data, child_row_index = find_row_by_id(children_sheet, child_id_str) # use find_row_by_id function and tuple unpacking to search the 'children_sheet' for given ID.

        if child_row_index == -1: # check if find_row_by_id returned an error signal (-1).
             return # exit if sheet access failed.
        
        # If child_data was found (not None).
        if child_data:
            child_name = f"{child_data[1]} {child_data[2]}" # construct child's name using list indexing.
            print(f"   Found Child: {child_name} (Age: {child_data[3]})") # print child's details for confirmation.
            break # break 'while' loop as child was found.
        else:
            print(f"Warning: Child with ID {child_id_str} not found.")  # if child not found, print a warning and contiue the loop.

    # Get and Validate Pet ID
    while True:
        pet_id_str = validate_input(
            "Enter ID of the Pet: ", # call validate_input helper function, pass the prompt to display to user.
            validate_integer, # pass validate_integer function
            "Warning: Invalid ID. Please enter the pet's ID number."
        )
        pet_data, pet_row_index = find_row_by_id(pets_sheet, pet_id_str) # use find_row_by_id function and tuple unpacking to search the 'pets_sheet' for given ID.

        if pet_row_index == -1: # check if find_row_by_id returned an error signal (-1).
             return # exit if sheet access failed.
        
        # If pet_data was found (not None).
        if pet_data:
            print(f"   Found Pet: {pet_data[1]} ({pet_data[3]}, Age: {pet_data[2]} months)") # print pets's details for confirmation (list indexing).
            break
        else:
            print(f"Warning: Pet with ID {pet_id_str} not found.") # if pet not found, print a warning and contiue the loop.

    # Check if child already has a pet linked
    try: # check if this child already has a link in the 'Owners' sheet.
        existing_link, _ = find_row_by_child_name(owners_sheet, child_name) # tuple unpacking, ignoring second value.
        if existing_link and len(existing_link) > 1 and existing_link[1]: # check if row is found and a Pet ID in the second column.
            print("-" * 10)
            print(f"Warning: Child '{child_name}' is already linked to Pet ID #{existing_link[1]}.") # warn the user about the existing link (it will be overwritten).
            if not confirm_action("Do you want to replace the existing link?"):  # ask if user wants to proceed to replace the existing link.
                print("   Operation cancelled.") # If confirm_action returns False, exit the link_child_pet function.
                return
        # Check if pet is already assigned to some child
        pet_link, _ = find_row_by_pet_id(owners_sheet, pet_id_str)
        if pet_link:
            print(f"Warning: Pet '{pet_data[1]}' (ID: {pet_id_str}) is already linked to '{pet_link[0]}'.") # if a link is found, warn the user.
            print("   Assigning this pet will remove its link from the previous owner.")

    except Exception as e:
         print(f"Warning: Error checking existing links: {e}")  # if an error occurs during check, print a warning.

    # Confirm linking
    print("-" * 10)
    link_prompt = f"Assign Pet '{pet_data[1]}' (ID #{pet_id_str}) to Child '{child_name}' (ID #{child_id_str})?" # detailed confirmation prompt.
    if confirm_action(link_prompt):
        try:
            owner_row_data, owner_row_index = find_row_by_child_name(owners_sheet, child_name) # if child exists in Owners, try to update, otherwise add new row.

            if owner_row_index == -1: # error during Owners check, exit.
                return

            # Handle Pet Reassignment
            prev_owner_row, prev_owner_index = find_row_by_pet_id(owners_sheet, pet_id_str) # check if this Pet ID exists in Owners sheet.
            if prev_owner_index and prev_owner_index != owner_row_index: # chech if pet was linked before and present in different row than the current child row.
                 print(f"   Clearing previous owner ({prev_owner_row[0]}) link to Pet ID #{pet_id_str}...")
                 owners_sheet.update_cell(prev_owner_index, 2, "") # clear Pet ID from the previous owner's row.
            
            # Add or Update Link
            if owner_row_data: # check if child was already found in the Owners sheet.
                owners_sheet.update_cell(owner_row_index, 2, int(pet_id_str)) # update the Pet ID.
                print(f"Success: Link updated in 'Owners' sheet (Row {owner_row_index}).") # confirm update.
            else:
                owners_sheet.append_row([child_name, int(pet_id_str)]) # if child not found, append a new row with Child Name and new Pet ID.
                print("Success: Link added to 'Owners' sheet.") # confirm append.

            print("-" * 10)
            print(f"Success: Successfully linked Child '{child_name}' and Pet '{pet_data[1]}'.") # show operation success message.
            print("-" * 10)

        # Handle Sheet Update Errors
        except gspread.exceptions.APIError as e:
            print(f"Error: Google Sheets API Error linking child/pet: {e}")
        except Exception as e:
            print(f"Error: An unexpected error occurred linking child/pet: {e}")
    else:
        print("   Operation cancelled.") # if confirm_action returned False (user choose "no")

def search_by_child():
    """Searches for the pet linked to a specific child."""
    print("\n- Search Pet by Child -")
    # Get and validate child ID
    child_id_str = validate_input( # validate_input to get a numeric string ID from the user.
        "Enter ID of the Child: ",
        validate_integer,
        "Warning: Invalid ID. Please enter the child's ID number."
    )
    # Find child in Children Sheet
    child_data, child_row_index = find_row_by_id(children_sheet, child_id_str) # use find_row_by_id function and tuple unpacking to find child in the 'children_sheet'.

    if child_row_index == -1: return # check if find_row_by_id returned an error signal (-1).
    if not child_data:
        print(f"Warning: Child with ID {child_id_str} not found in 'Children' sheet.") # if not found, warn and exit function.
        return
    # Construct child name and inform user
    child_name = f"{child_data[1]} {child_data[2]}" # construct child's full name.
    print(f"   Searching for pet linked to: {child_name} (Age: {child_data[3]})") # looking for a pet linked to a child.

    # Search for child-pet link in Owners sheet
    try:
        owner_row, owner_row_index = find_row_by_child_name(owners_sheet, child_name) # use find_row_by_child_name function to find child's entry in 'owners_sheet'.

        if owner_row_index == -1: return # check if find_row_by_id returned an error signal (-1).

        # Check if child is linked to a pet
        if owner_row and len(owner_row) > 1 and owner_row[1]: # check if row has at least two columns and if the second column (Pet ID, index 1) is not empty.
            pet_id_str = owner_row[1] # get Pet ID string from the second column of the owner row.
            pet_data, pet_row_index = find_row_by_id(pets_sheet, pet_id_str) # use find_row_by_id function to find the corresponding pet in the 'pets_sheet'.
            if pet_row_index == -1: return # check if find_row_by_id returned an error signal (-1).
            if pet_data: # if found, print details of child and linked pet.
                print("-" * 10)
                print(f"Success: Found Link:") 
                print(f"   Child: {child_name} (ID #{child_id_str})")
                print(f"   Pet:   {pet_data[1]} (ID #{pet_id_str}), Type: {pet_data[3]}, Age: {pet_data[2]} months")
                print("-" * 10)
            else: # in not found (link exists in Owners but pet doesn't exist in the Pets), warn about data inconsistency.
                print("-" * 10)
                print(f"Warning: Found link for {child_name} to Pet ID #{pet_id_str}, but this pet doesn't exist in the 'Pets' sheet.")
                print("   Please check data consistency.")
                print("-" * 10)
        else: # if owner_row not found, or if Pet ID column empty, inform that child has no linked pet.
            print("-" * 10)
            print(f"Info: Child '{child_name}' (ID #{child_id_str}) is not currently linked to any pet in the 'Owners' sheet.")
            print("-" * 10)
    # Handle Errors during Sheet Access
    except gspread.exceptions.APIError as e:
        print(f"Error: Google Sheets API Error searching by child: {e}") # if error related to the Google Sheets API
    except Exception as e:
        print(f"Error: An unexpected error occurred searching by child: {e}") # any unexpected errors during the search.

def search_by_pet():
    """Searches for the child linked to a specific pet."""
    print("\n- Search Child by Pet -")
    # Get and validate pet ID
    pet_id_str = validate_input( # validate_input to get a numeric string ID from the user.
        "Enter ID of the Pet: ",
        validate_integer,
        "Warning: Invalid ID. Please enter the pet's ID number."
    )

    # Find pet in Pets Sheet
    pet_data, pet_row_index = find_row_by_id(pets_sheet, pet_id_str) # use find_row_by_id function and tuple unpacking to find child in the 'pets_sheet'.

    if pet_row_index == -1: return # check if find_row_by_id returned an error signal (-1).
    if not pet_data:
        print(f"Warning: Pet with ID {pet_id_str} not found in 'Pets' sheet.") # if not found, warn and exit function.
        return

    print(f"   Searching for child linked to: {pet_data[1]} ({pet_data[3]}, Age: {pet_data[2]} months)") # looking for a child linked with a pet

    # Search for pet-child link in Owners sheet
    try:
        owner_row, owner_row_index = find_row_by_pet_id(owners_sheet, pet_id_str) # use find_row_by_pet_id function to find pet's entry in 'owners_sheet'.

        if owner_row_index == -1: return # check if find_row_by_id returned an error signal (-1).
        
        # Check if Pet is Linked to a Child
        if owner_row: # сheck if a row was found (Pet ID is already present because find_row_by_pet_id was succeefull).
            child_name = owner_row[0] # get Child's full name from the first column (index 0) of the owner row.

            # Find Child Details in Children Sheet by Name
            child_details_found = False # flag tracks whether this iteration was successful after the loop has finished.
            all_children = children_sheet.get_all_values() # get data from the children sheet.
            for child_row in all_children[1:]: # loop through each child row, skipping header row (index 0).
                if child_row and f"{child_row[1]} {child_row[2]}" == child_name: # if row exist, construct the full name and compare with the 'child_name'.
                    print("-" * 10)
                    print(f"Success: Found Link:") 
                    print(f"   Pet:   {pet_data[1]} (ID #{pet_id_str})")
                    print(f"   Child: {child_name} (ID #{child_row[0]}), Age: {child_row[3]}") # show child details.
                    print("-" * 10)
                    child_details_found = True # set flag to True and exit the loop when child is found.
                    break
            if not child_details_found: # in not found (link exists in Owners but child doesn't exist in the Children), warn about data inconsistency.
                print("-" * 10)
                print(f"Warning: Found link for Pet ID #{pet_id_str} to '{child_name}', but this child doesn't exist in the 'Children' sheet.")
                print("   Please check data consistency.")
                print("-" * 10)

        else: # if owner_row not found for this Pet ID column empty, inform that pet is not linked to any child.
            print("-" * 10)
            print(f"Info: Pet '{pet_data[1]}' (ID #{pet_id_str}) is not currently linked to any child in the 'Owners' sheet.")
            print("-" * 10)

    # Handle Errors during Sheet Access
    except gspread.exceptions.APIError as e:
        print(f"Error: Google Sheets API Error searching by pet: {e}") # if error related to the Google Sheets API
    except Exception as e:
        print(f"Error: An unexpected error occurred searching by pet: {e}") # any unexpected errors during the search.

def delete_child():
    """Deletes a child from 'Children' and corresponding row in 'Owners'."""
    print("\n- Delete Child -")
    # Get and Validate child ID
    child_id_str = validate_input( # validate_input to get a numeric string ID from the user.
        "Enter ID of the Child to delete: ",
        validate_integer,
        "Warning: Invalid ID. Please enter the child's ID number."
    )

    # Find child in Children Sheet
    child_data, child_row_index = find_row_by_id(children_sheet, child_id_str) # use find_row_by_id function and tuple unpacking to find child in the 'children_sheet'.

    if child_row_index == -1: return # check if find_row_by_id returned an error signal (-1).
    if not child_data:
        print(f"Warning: Child with ID {child_id_str} not found.") # if not found, warn and exit function.
        return
    # Construct child name and inform user
    child_name = f"{child_data[1]} {child_data[2]}" # construct child's full name.
    print("-" * 10)
    print(f"   Child Found: {child_name} (Age: {child_data[3]}) - ID #{child_id_str}") # show which child was found.
    print("   Warning: Deleting this child will also remove their entry from the 'Owners' sheet.") # warn about removing the link too.
    print("-" * 10)

    # Confirm Deletion
    delete_prompt = f"Are you sure you want to delete child '{child_name}' (ID #{child_id_str})?"
    if confirm_action(delete_prompt): # call confirm_action and proceed only if it returns True.
        try: # try block for sheet modification (may fail).
            children_sheet.delete_rows(child_row_index) # delete from Children sheet (delete_rows method, pass row index).
            print(f"   Deleted row {child_row_index} from 'Children' sheet.")

            # Find and delete from Owners sheet
            owner_row, owner_row_index = find_row_by_child_name(owners_sheet, child_name)  # search 'owners_sheet' for matching the child's name.
            if owner_row_index == -1: # check if find_row_by_child_name returned an error signal (-1).
                print("Warning: Could not check 'Owners' sheet due to an error, but child deleted from 'Children'.")  # child already deleted from the Children sheet at this point.
            elif owner_row:
                owners_sheet.delete_rows(owner_row_index) # if owner_row exist, delete row using index.
                print(f"   Deleted row {owner_row_index} from 'Owners' sheet.")
            else:
                print("   Info: No corresponding entry found in 'Owners' sheet.") # if owner_row not exist, inform that no deletion needed.

            print("-" * 10)
            print(f"Success: Child '{child_name}' successfully deleted.") # show operation success message.
            print("-" * 10)

        # Handle Errors during Sheet Access
        except gspread.exceptions.APIError as e:
            print(f"Error: Google Sheets API Error deleting child: {e}") # if error related to the Google Sheets API
        except Exception as e:
            print(f"Error: An unexpected error occurred deleting child: {e}") # any unexpected errors during the search.
    else:
        print("   Deletion cancelled.")

def delete_pet():
    """Deletes a pet from 'Pets' and clears the link in 'Owners'."""
    print("\n- Delete Pet -")
    pet_id_str = validate_input( # validate_input to get a numeric string ID from the user.
        "Enter ID of the Pet to delete: ",
        validate_integer,
        "Warning: Invalid ID. Please enter the pet's ID number."
    )

    # Find pet in Pets Sheet
    pet_data, pet_row_index = find_row_by_id(pets_sheet, pet_id_str) # use find_row_by_id function and tuple unpacking to find pet in the 'pet_sheet'.

    if pet_row_index == -1: return # check if find_row_by_id returned an error signal (-1).
    if not pet_data:
        print(f"Warning: Pet with ID {pet_id_str} not found.") # if not found, warn and exit function.
        return

    # Show pet data and inform user
    print("-" * 10)
    print(f"   Pet Found: {pet_data[1]} ({pet_data[3]}, Age: {pet_data[2]} months) - ID #{pet_id_str}") # show which pet was found.
    print("   Warning: Deleting this pet will also clear its assignment in the 'Owners' sheet.") # warn about removing the link too.
    print("-" * 10)

    # Confirm Deletion
    delete_prompt = f"Are you sure you want to delete Pet '{pet_data[1]}' (ID #{pet_id_str})?"
    if confirm_action(delete_prompt): # call confirm_action and proceed only if it returns True.
        try: # try block for sheet modification (may fail).
            pets_sheet.delete_rows(pet_row_index) # delete from Pet sheet (delete_rows method, pass row index).
            print(f"   Deleted row {pet_row_index} from 'Pets' sheet.")

            # Find and delete from Owners sheet
            owner_row, owner_row_index = find_row_by_pet_id(owners_sheet, pet_id_str) # search 'owners_sheet' for matching the pet's ID.

            if owner_row_index == -1: # # check if find_row_by_pet_id returned an error signal (-1).
                print("Warning: Could not check 'Owners' sheet due to an error, but pet deleted from 'Pets'.") # pet already deleted from the Pets sheet at this point.
            elif owner_row:
                owners_sheet.update_cell(owner_row_index, 2, "") # if owner_row exist, clear the Pet ID cell using update_cell takes and "" value. 
                print(f"   Cleared Pet ID link in 'Owners' sheet (Row {owner_row_index}).")
            else:
                print("   Info: No corresponding link found in 'Owners' sheet.") # if owner_row not exist, inform that no deletion needed.

            print("-" * 10)
            print(f"Success: Pet '{pet_data[1]}' successfully deleted.") # show operation success message.
            print("-" * 10)

        # Handle Errors during Sheet Access
        except gspread.exceptions.APIError as e:
            print(f"Error: Google Sheets API Error deleting pet: {e}") # if error related to the Google Sheets API
        except Exception as e:
            print(f"Error: An unexpected error occurred deleting pet: {e}") # any unexpected errors during the search.
    else:
        print("   Deletion cancelled.")

def exit_app():
    """Exits the application."""
    print("\nThank you for using Forever Home Friends!")
    sys.exit() # call sys.exit from imported 'sys' module for clean exit from the script.

# Main Application Loop
def main():
    """Runs the main application menu loop."""
    print("Welcome to Forever Home Friends!")

    while True: # 'while True' loop runs until explicitly stopped by sys.exit, keeps the menu displaying after each action.
        print("\n- Main Menu -")
        print("1. Add a Child")
        print("2. Add a Pet")
        print("3. Link Child and Pet")
        print("4. Search Pet by Child ID")
        print("5. Search Child by Pet ID")
        print("6. Delete a Child by ID")
        print("7. Delete a Pet by ID")
        print("8. Exit Application")
        print("-" * 30)

        choice = input("Please enter your choice (1-8): ").strip()  # prompt the user and get input string removing whitespace.

        if choice == '1': # if/elif/else structure to check the user's choice.
            add_child()
        elif choice == '2':
            add_pet()
        elif choice == '3':
            link_child_pet()
        elif choice == '4':
            search_by_child()
        elif choice == '5':
            search_by_pet()
        elif choice == '6':
            delete_child()
        elif choice == '7':
            delete_pet()
        elif choice == '8':
            exit_app()
        else:
            print("Warning: Invalid choice. Please enter a number between 1 and 8.") # if the input doesn't match any choice 
        
        input("\nPress Enter to return to the main menu...") # pause so the the user can easily see the output.
# Run the application
if __name__ == "__main__": # ensure that main function is called only when we run run.py directly from the command line.
    main()