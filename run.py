import sys  # Used to terminate the execution of the Python script.
import gspread  # Tools to easily work with the content of Google Sheets
# Credentials class to handle the authentication
from google.oauth2.service_account import Credentials

# Google Sheets API scope
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials and authorize with error handling
try:
    CREDS = Credentials.from_service_account_file('creds.json')
    # scope the Google APIs script needs access to
    SCOPED_CREDS = CREDS.with_scopes(SCOPE)
    # authenticated client object
    GSPREAD_CLIENT = gspread.authorize(SCOPED_CREDS)
    SHEET = GSPREAD_CLIENT.open('forever_home_friends')  # open Google Sheet
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
        # If sheet has more than one row (header + data),
        # take all rows starting from second row (index 1).
        # Otherwise (if only 0 or 1 row), create an empty list for data_rows.
        data_rows = all_values[1:] if len(all_values) > 1 else []
        if not data_rows:
            return 1  # If there's no data, the first ID is set to 1.
        # Find the highest existing ID
        # Initialize a variable to store the maximum ID found.
        max_id = 0
        for row in data_rows:
            # Check if row exists and first cell is digit to avoid errors.
            if row and row[0].isdigit():
                # Convert ID to integer, update max_id if the current row ID
                # is greater than current max_id.
                max_id = max(max_id, int(row[0]))
        # Calculate and return the next ID
        return max_id + 1
    # If any error occurs during the 'try' block, print a warning message
    # with error details.
    except Exception as e:
        print(f"Warning: Error retrieving next ID: {e}")
        # Return None if failed to get an ID for calling functions
        # (like add_child and add_pet).
        return None


def validate_input(prompt, validation_func, error_message, **kwargs):
    """
    Generic function to validate user input.

        prompt (str): Message displayed to user.
        validation_func (callable): Function to validate input (True if valid).
        error_message (str): Message displayed on invalid input.
        **kwargs: Additional arguments to pass.
    Returns:
        str: Validated user input.
    """
    while True:  # start an infinite loop that break when on valid input
        # removes any leading/trailing spaces.
        user_input = input(prompt).strip()
        if not user_input:  # print a warning for empty input.
            print("Warning: Input cannot be empty. Please try again.")
            continue  # skips the rest of the loop and asks for input again.
        # if validation_func returns True, return the valid user input.
        if validation_func(user_input, **kwargs):
            return user_input
        else:  # If validation_func returns False, print the error_message.
            print(error_message)


def validate_integer(input_str):
    """Checks if the input string is a valid integer."""
    # check if all characters are digits
    # to ensure the user entered a number (like add ID).
    return input_str.isdigit()


def validate_range(input_str, min_val, max_val):
    """Checks if input is an integer within a specified range."""
    if not input_str.isdigit():  # check if all characters are digits.
        return False
    value = int(input_str)  # convert the input string to integer number
    # check if that number falls within the specified inclusive range
    # (like add age).
    return min_val <= value <= max_val


def confirm_action(prompt):
    """Asks for Yes/No confirmation (accepts y/n)."""
    while True:
        # ask user a question and only accept "y" or "n" as valid answers.
        choice = input(f"{prompt} (y/n): ").strip().lower()
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
    # check if provided 'id_str' actually contains only digits.
    if not id_str.isdigit():
        return None, None  # input format is wrong.

    try:  # attempt Sheet access
        # fetch all rows and columns from specified worksheet.
        all_values = worksheet.get_all_values()
        # provides index of the row and row data.
        for index, row in enumerate(all_values):
            # compare value in the first cell (row[0]) with 'id_str'.
            if row and row[0] == id_str:
                # return tuple: list of data for matching row and row number.
                return row, index + 1
        return None, None  # no row with the specified ID was found.
    except gspread.exceptions.APIError as e:
        # if error related to the Google Sheets API
        print(f"Error: Google Sheets API Error: {e}")
        print("   Please check your connection and permissions.")
        # -1 indicate error occurred during search, not that row wasn't found
        # (returns None, None).
        return None, -1
    except Exception as e:  # catch other unexpected errors during 'try'.
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
        # fetch all rows and columns from specified worksheet.
        all_values = worksheet.get_all_values()
        # provides index of the row and row data.
        for index, row in enumerate(all_values):
            # check if row has at least one column, compare value
            # in the first cell with the 'full_name' string.
            if row and len(row) > 0 and row[0] == full_name:
                # return list of data for matching row (Child Name, Pet ID)
                return row, index + 1
        return None, None  # no row with the specified child's name was found.
    except gspread.exceptions.APIError as e:
        print(f"Error: Google Sheets API Error: {e}")
        print("   Please check your connection and permissions.")
        # -1 indicate error occurred during search, not that name wasn't found
        # (returns None, None).
        return None, -1
    except Exception as e:  # catch other unexpected errors during 'try'.
        print("Warning: An unexpected error occurred "
              f"finding row by name: {e}")
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
    # check if provided 'pet_id_str' actually contains only digits.
    if not pet_id_str.isdigit():
        return None, None  # input format is wrong.

    try:
        # fetch all rows and columns from specified worksheet.
        all_values = worksheet.get_all_values()
        # provides index of the row and row data.
        for index, row in enumerate(all_values):
            # check if row has at least two columns, compare value
            # in the second cell with the 'pet_id_str' string.
            if row and len(row) > 1 and row[1] == pet_id_str:
                # return list of data for matching row (Child Name, Pet ID)
                return row, index + 1
        return None, None  # no row with the specified Pet ID was found.
    except gspread.exceptions.APIError as e:
        print(f"Error: Google Sheets API Error: {e}")
        print("   Please check your connection and permissions.")
        # -1 indicate error occurred during search, not that ID wasn't found
        # (returns None, None).
        return None, -1
    except Exception as e:  # catch other unexpected errors during 'try'.
        print(f"Warning: An unexpected error finding row by pet ID: {e}")
        return None, -1


# Core Functions Section (Menu Options)

def add_child():
    """Adds a new child record to the 'Children' sheet."""
    print("\n- Add New Child -")
    # ask for the first name, remove extra whitespace, make first letter upper.
    first_name = input("Enter Child's First Name: ").strip().capitalize()
    if not first_name:  # if empty, print a warning and exit.
        print("Warning: First name cannot be empty.")
        return

    # ask for the last name, remove extra whitespace, make first letter upper.
    last_name = input("Enter Child's Last Name: ").strip().capitalize()
    if not last_name:  # if empty, print a warning and exit.
        print("Warning: Last name cannot be empty.")
        return

    # Get and Validate Age (valid number string between 5 and 18 years).
    age_str = validate_input(
        # call validate_input helper function, pass prompt to display to user.
        "Enter Child's Age (5-18 years): ",
        # pass validation func using anonymous 'lambda' that calls
        # 'validate_range' ensuring 'x' between 5 and 18.
        lambda x: validate_range(x, min_val=5, max_val=18),
        "Warning: Invalid age. Please enter a number between 5 and 18."
    )

    # Get the Next Available ID
    next_id = get_next_id(children_sheet)  # call the get_next_id helper func
    # check if returned None, indicates error trying to get the ID.
    if next_id is None:
        print("Error: Could not determine next ID. Aborting.")
        return

    # Prepare the New Row Data
    # convert age string to an integer and create list containing data
    # for the new row.
    new_child_data = [next_id, first_name, last_name, int(age_str)]

    # Try to Append Data to Google Sheet
    try:  # 'try' block as access to Google Sheets can fail.
        # 'append_row' method to add 'new_child_data' list as new bottom row.
        children_sheet.append_row(new_child_data)
        print("-" * 10)
        # if append is ok, show a confirmation message
        print(f"Success: Child '{first_name} {last_name}' added successfully!")
        print(f"   Assigned ID: {next_id}")
        print("-" * 10)
    except gspread.exceptions.APIError as e:  # specific errors for Sheets API
        print(f"Error: Google Sheets API Error adding child: {e}")
        print("   Check your connection and permissions.")
    except Exception as e:  # any unexpected errors during the append.
        print(f"Error: An unexpected error occurred adding child: {e}")


def add_pet():
    """Adds a new pet record to the 'Pets' sheet."""
    print("\n- Add New Pet -")
    # ask for the Pet's Nickname, remove extra whitespace, make first upper.
    nickname = input("Enter Pet's Nickname: ").strip().capitalize()
    if not nickname:  # if empty, print a warning and exit.
        print("Warning: Nickname cannot be empty.")
        return

    # Get and Validate Age (valid number string between 0 and 12 months).
    age_str = validate_input(
        # call validate_input helper function, pass prompt to display to user.
        "Enter Pet's Age (0-12 months): ",
        # pass validation func using anonymous 'lambda' that calls
        # 'validate_range' ensuring 'x' between 0 and 12.
        lambda x: validate_range(x, min_val=0, max_val=12),
        "Warning: Invalid age. Please enter a number between 0 and 12."
    )
    # Get and Validate Pet Type
    pet_type_short = validate_input(
        # call validate_input helper function, pass prompt to display to user.
        "Enter Pet Type (p for puppy / k for kitty): ",
        # lambda function to ensure the validated input is lowercase ('p'/'k').
        lambda x: x.lower() in ['p', 'k'],
        "Warning: Invalid type. Please enter 'p' or 'k'."
    ).lower()  # ensure that final value is always lowercase.

    # Convert 'p' / 'k' to 'puppy' / 'kitty'for storage
    if pet_type_short == 'p':
        pet_type = 'puppy'
    elif pet_type_short == 'k':
        pet_type = 'kitty'
    else:
        # fallback in case of error.
        print("Error: Unexpected error processing pet type. Aborting.")
        return

    # Get the Next Available ID
    next_id = get_next_id(pets_sheet)  # call the get_next_id helper function
    # check if returned None, indicates error trying to get the ID.
    if next_id is None:
        print("Error: Could not determine next ID. Aborting.")
        return

    # convert age str to int and create list containing data for new row.
    new_pet_data = [next_id, nickname, int(age_str), pet_type]

    # Try to Append Data to Google Sheet
    try:  # 'try' block as access to Google Sheets can fail.
        # 'append_row' method to add 'new_pet_data' list as new bottom row.
        pets_sheet.append_row(new_pet_data)
        print("-" * 10)
        # if append is ok, show a confirmation message
        print(f"Success: Pet '{nickname}' ({pet_type}) added successfully!")
        print(f"   Assigned ID: {next_id}")
        print("-" * 10)
    except gspread.exceptions.APIError as e:  # specific errors for Sheets API.
        print(f"Error: Google Sheets API Error adding pet: {e}")
        print("   Check your connection and permissions.")
    except Exception as e:  # any unexpected errors during the append.
        print(f"Error: An unexpected error occurred adding pet: {e}")


def link_child_pet():
    """Links a child to a pet in the 'Owners' sheet."""
    print("\n- Link Child and Pet -")

    # Get and Validate Child ID
    while True:
        child_id_str = validate_input(
            # call validate_input helper function, pass prompt to display user.
            "Enter ID of the Child: ",
            validate_integer,  # pass validate_integer function
            "Warning: Invalid ID. Please enter the child's ID number."
        )
        # use find_row_by_id function and tuple unpacking to search
        # the 'children_sheet' for given ID.
        child_data, child_row_index = find_row_by_id(children_sheet,
                                                     child_id_str)

        # check if find_row_by_id returned an error signal (-1).
        if child_row_index == -1:
            return  # exit if sheet access failed.

        # If child_data was found (not None).
        if child_data:
            # construct child's name using list indexing.
            child_name = f"{child_data[1]} {child_data[2]}"
            # print child's details for confirmation.
            print(f"   Found Child: {child_name} (Age: {child_data[3]})")
            break  # break 'while' loop as child was found.
        else:
            # if child not found, print a warning and contiue the loop.
            print(f"Warning: Child with ID {child_id_str} not found.")

    # Get and Validate Pet ID
    while True:
        pet_id_str = validate_input(
            # call validate_input helper function, pass prompt to display user.
            "Enter ID of the Pet: ",
            validate_integer,  # pass validate_integer function
            "Warning: Invalid ID. Please enter the pet's ID number."
        )
        # use find_row_by_id function and tuple unpacking to search
        # the 'pets_sheet' for given ID.
        pet_data, pet_row_index = find_row_by_id(pets_sheet, pet_id_str)

        # check if find_row_by_id returned an error signal (-1).
        if pet_row_index == -1:
            return  # exit if sheet access failed.

        # If pet_data was found (not None).
        if pet_data:
            # print pets's details for confirmation (list indexing).
            print(f"   Found Pet: {pet_data[1]} ({pet_data[3]}, "
                  f"Age: {pet_data[2]} months)")
            break
        else:
            # if pet not found, print a warning and contiue the loop.
            print(f"Warning: Pet with ID {pet_id_str} not found.")

    # Check if child already has a pet linked
    try:  # check if this child already has a link in the 'Owners' sheet.
        # tuple unpacking, ignoring second value.
        existing_link, _ = find_row_by_child_name(owners_sheet, child_name)
        # check if row is found and a Pet ID in the second column.
        if existing_link and len(existing_link) > 1 and existing_link[1]:
            print("-" * 10)
            # warn the user about existing link (it will be overwritten).
            print(f"Warning: Child '{child_name}' is already linked to "
                  f"Pet ID #{existing_link[1]}.")
            # ask if user wants to proceed to replace the existing link.
            if not confirm_action("Do you want to replace the existing link?"):
                # If confirm_action returns False, exit the function.
                print("   Operation cancelled.")
                return
        # Check if pet is already assigned to some child
        pet_link, _ = find_row_by_pet_id(owners_sheet, pet_id_str)
        if pet_link:
            # if a link is found, warn the user.
            print(f"Warning: Pet '{pet_data[1]}' (ID: {pet_id_str}) "
                  f"is already linked to '{pet_link[0]}'.")
            print("   Assigning this pet will remove its link "
                  "from the previous owner.")

    except Exception as e:
        # if an error occurs during check, print a warning.
        print(f"Warning: Error checking existing links: {e}")

    # Confirm linking
    print("-" * 10)
    # detailed confirmation prompt.
    link_prompt = (f"Assign Pet '{pet_data[1]}' (ID #{pet_id_str}) to "
                   f"Child '{child_name}' (ID #{child_id_str})?")
    if confirm_action(link_prompt):
        try:
            # if child exists in Owners, try to update, otherwise add new row.
            owner_row_data, owner_row_index = find_row_by_child_name(
                owners_sheet, child_name
            )

            if owner_row_index == -1:  # error during Owners check, exit.
                return

            # Handle Pet Reassignment
            # check if this Pet ID exists in Owners sheet.
            prev_owner_row, prev_owner_index = find_row_by_pet_id(
                owners_sheet, pet_id_str
            )
            # check if pet was linked before and present in different row
            # than the current child row.
            if prev_owner_index and prev_owner_index != owner_row_index:
                print(f"   Clearing previous owner ({prev_owner_row[0]}) "
                      f"link to Pet ID #{pet_id_str}...")
                # clear Pet ID from the previous owner's row.
                owners_sheet.update_cell(prev_owner_index, 2, "")

            # Add or Update Link
            # check if child was already found in the Owners sheet.
            if owner_row_data:
                owners_sheet.update_cell(owner_row_index, 2, int(pet_id_str))
                # confirm update.
                print(f"Success: Link updated in 'Owners' sheet "
                      f"(Row {owner_row_index}).")
            else:
                # if child not found, append a new row with Child Name
                # and new Pet ID.
                owners_sheet.append_row([child_name, int(pet_id_str)])
                print("Success: Link added to 'Owners' sheet.")  # append ok.

            print("-" * 10)
            # show operation success message.
            print(f"Success: Successfully linked Child '{child_name}' "
                  f"and Pet '{pet_data[1]}'.")
            print("-" * 10)

        # Handle Sheet Update Errors
        except gspread.exceptions.APIError as e:
            print(f"Error: Google Sheets API Error linking child/pet: {e}")
        except Exception as e:
            print("Error: An unexpected error occurred "
                  f"linking child/pet: {e}")
    else:
        # if confirm_action returned False (user choose "no")
        print("   Operation cancelled.")


def search_by_child():
    """Searches for the pet linked to a specific child."""
    print("\n- Search Pet by Child -")
    # Get and validate child ID
    # validate_input to get a numeric string ID from the user.
    child_id_str = validate_input(
        "Enter ID of the Child: ",
        validate_integer,
        "Warning: Invalid ID. Please enter the child's ID number."
    )
    # Find child in Children Sheet
    # use find_row_by_id func and tuple unpacking to find child
    # in the 'children_sheet'.
    child_data, child_row_index = find_row_by_id(children_sheet, child_id_str)

    if child_row_index == -1:
        return  # check if find_row_by_id returned an error signal (-1).
    if not child_data:
        # if not found, warn and exit function.
        print(f"Warning: Child with ID {child_id_str} not found "
              "in 'Children' sheet.")
        return
    # Construct child name and inform user
    child_name = f"{child_data[1]} {child_data[2]}"  # construct child's name.
    # looking for a pet linked to a child.
    print(f"   Searching for pet linked to: {child_name} "
          f"(Age: {child_data[3]})")

    # Search for child-pet link in Owners sheet
    try:
        # use find_row_by_child_name func to find child's entry
        # in 'owners_sheet'.
        owner_row, owner_row_index = find_row_by_child_name(owners_sheet,
                                                            child_name)

        if owner_row_index == -1:
            return  # check if find_row_by_id returned an error signal (-1).

        # Check if child is linked to a pet
        # check if row has at least two columns and if the second column
        # (Pet ID, index 1) is not empty.
        if owner_row and len(owner_row) > 1 and owner_row[1]:
            # get Pet ID string from the second column of the owner row.
            pet_id_str = owner_row[1]
            # use find_row_by_id function to find the corresponding pet
            # in the 'pets_sheet'.
            pet_data, pet_row_index = find_row_by_id(pets_sheet, pet_id_str)
            if pet_row_index == -1:
                return  # check if find_row_by_id returned error signal (-1).
            if pet_data:  # if found, print details of child and linked pet.
                print("-" * 10)
                print("Success: Found Link:")
                print(f"   Child: {child_name} (ID #{child_id_str})")
                print(f"   Pet:   {pet_data[1]} (ID #{pet_id_str}), "
                      f"Type: {pet_data[3]}, Age: {pet_data[2]} months")
                print("-" * 10)
            else:
                # if not found (link exists in Owners but pet doesn't exist
                # in the Pets), warn about data inconsistency.
                print("-" * 10)
                print(f"Warning: Found link for {child_name} to Pet ID "
                      f"#{pet_id_str}, but this pet doesn't exist in the "
                      "'Pets' sheet.")
                print("   Please check data consistency.")
                print("-" * 10)
        else:
            # if owner_row not found, or if Pet ID column empty, inform that
            # child has no linked pet.
            print("-" * 10)
            print(f"Info: Child '{child_name}' (ID #{child_id_str}) is not "
                  "currently linked to any pet in the 'Owners' sheet.")
            print("-" * 10)
    # Handle Errors during Sheet Access
    except gspread.exceptions.APIError as e:
        # if error related to the Google Sheets API
        print(f"Error: Google Sheets API Error searching by child: {e}")
    except Exception as e:
        # any unexpected errors during the search.
        print(f"Error: An unexpected error occurred searching by child: {e}")


def search_by_pet():
    """Searches for the child linked to a specific pet."""
    print("\n- Search Child by Pet -")
    # Get and validate pet ID
    # validate_input to get a numeric string ID from the user.
    pet_id_str = validate_input(
        "Enter ID of the Pet: ",
        validate_integer,
        "Warning: Invalid ID. Please enter the pet's ID number."
    )

    # Find pet in Pets Sheet
    # use find_row_by_id function and tuple unpacking to find child
    # in the 'pets_sheet'.
    pet_data, pet_row_index = find_row_by_id(pets_sheet, pet_id_str)

    if pet_row_index == -1:
        return  # check if find_row_by_id returned an error signal (-1).
    if not pet_data:
        # if not found, warn and exit function.
        print(f"Warning: Pet with ID {pet_id_str} not found in 'Pets' sheet.")
        return

    # looking for a child linked with a pet
    print(f"   Searching for child linked to: {pet_data[1]} "
          f"({pet_data[3]}, Age: {pet_data[2]} months)")

    # Search for pet-child link in Owners sheet
    try:
        # use find_row_by_pet_id function to find pet's entry in 'owners_sheet'
        owner_row, owner_row_index = find_row_by_pet_id(owners_sheet,
                                                        pet_id_str)

        if owner_row_index == -1:
            return  # check if find_row_by_id returned an error signal (-1).

        # Check if Pet is Linked to a Child
        # check if a row was found (Pet ID is already present because
        # find_row_by_pet_id was succeefull).
        if owner_row:
            # get Child's full name from the first column (index 0)
            # of the owner row.
            child_name = owner_row[0]

            # Find Child Details in Children Sheet by Name
            # flag tracks whether this iteration was successful
            # after the loop has finished.
            child_details_found = False
            # get data from the children sheet.
            all_children = children_sheet.get_all_values()
            # loop through each child row, skipping header row (index 0).
            for child_row in all_children[1:]:
                # if row exist, construct the full name and compare
                # with the 'child_name'.
                if (child_row and
                        f"{child_row[1]} {child_row[2]}" == child_name):
                    print("-" * 10)
                    print("Success: Found Link:")
                    print(f"   Pet:   {pet_data[1]} (ID #{pet_id_str})")
                    # show child details.
                    print(f"   Child: {child_name} (ID #{child_row[0]}), "
                          f"Age: {child_row[3]}")
                    print("-" * 10)
                    # set flag to True and exit loop when child is found.
                    child_details_found = True
                    break
            # if not found (link exists in Owners but child doesn't exist
            # in the Children), warn about data inconsistency.
            if not child_details_found:
                print("-" * 10)
                print(f"Warning: Found link for Pet ID #{pet_id_str} to "
                      f"'{child_name}', but this child doesn't exist in "
                      "the 'Children' sheet.")
                print("   Please check data consistency.")
                print("-" * 10)

        else:
            # if owner_row not found for this Pet ID column empty,
            # inform that pet is not linked to any child.
            print("-" * 10)
            print(f"Info: Pet '{pet_data[1]}' (ID #{pet_id_str}) is not "
                  "currently linked to any child in the 'Owners' sheet.")
            print("-" * 10)

    # Handle Errors during Sheet Access
    except gspread.exceptions.APIError as e:
        # if error related to the Google Sheets API
        print(f"Error: Google Sheets API Error searching by pet: {e}")
    except Exception as e:
        # any unexpected errors during the search.
        print(f"Error: An unexpected error occurred searching by pet: {e}")


def delete_child():
    """Deletes a child from 'Children' and corresponding row in 'Owners'."""
    print("\n- Delete Child -")
    # Get and Validate child ID
    # validate_input to get a numeric string ID from the user.
    child_id_str = validate_input(
        "Enter ID of the Child to delete: ",
        validate_integer,
        "Warning: Invalid ID. Please enter the child's ID number."
    )

    # Find child in Children Sheet
    # use find_row_by_id function and tuple unpacking to find child
    # in the 'children_sheet'.
    child_data, child_row_index = find_row_by_id(children_sheet, child_id_str)

    if child_row_index == -1:
        return  # check if find_row_by_id returned an error signal (-1).
    if not child_data:
        # if not found, warn and exit function.
        print(f"Warning: Child with ID {child_id_str} not found.")
        return
    # Construct child name and inform user
    child_name = f"{child_data[1]} {child_data[2]}"  # construct child's name.
    print("-" * 10)
    # show which child was found.
    print(f"   Child Found: {child_name} (Age: {child_data[3]}) "
          f"- ID #{child_id_str}")
    # warn about removing the link too.
    print("   Warning: Deleting this child will also remove "
          "their entry from the 'Owners' sheet.")
    print("-" * 10)

    # Confirm Deletion
    delete_prompt = (f"Are you sure you want to delete child '{child_name}' "
                     f"(ID #{child_id_str})?")
    # call confirm_action and proceed only if it returns True.
    if confirm_action(delete_prompt):
        try:  # try block for sheet modification (may fail).
            # delete from Children sheet (delete_rows method, pass row index).
            children_sheet.delete_rows(child_row_index)
            print(f"   Deleted row {child_row_index} from 'Children' sheet.")

            # Find and delete from Owners sheet
            # search 'owners_sheet' for matching the child's name.
            owner_row, owner_row_index = find_row_by_child_name(owners_sheet,
                                                                child_name)
            # check if find_row_by_child_name returned an error signal (-1).
            if owner_row_index == -1:
                # child already deleted from the Children sheet at this point.
                print("Warning: Could not check 'Owners' sheet "
                      "due to an error, but child deleted from 'Children'.")
            elif owner_row:
                # if owner_row exist, delete row using index.
                owners_sheet.delete_rows(owner_row_index)
                print(f"   Deleted row {owner_row_index} from 'Owners' sheet.")
            else:
                # if owner_row not exist, inform that no deletion needed.
                print("   Info: No corresponding entry found in "
                      "'Owners' sheet.")

            print("-" * 10)
            # show operation success message.
            print(f"Success: Child '{child_name}' successfully deleted.")
            print("-" * 10)

        # Handle Errors during Sheet Access
        except gspread.exceptions.APIError as e:
            # if error related to the Google Sheets API
            print(f"Error: Google Sheets API Error deleting child: {e}")
        except Exception as e:
            # any unexpected errors during the search.
            print(f"Error: An unexpected error occurred deleting child: {e}")
    else:
        print("   Deletion cancelled.")


def delete_pet():
    """Deletes a pet from 'Pets' and clears the link in 'Owners'."""
    print("\n- Delete Pet -")
    # validate_input to get a numeric string ID from the user.
    pet_id_str = validate_input(
        "Enter ID of the Pet to delete: ",
        validate_integer,
        "Warning: Invalid ID. Please enter the pet's ID number."
    )

    # Find pet in Pets Sheet
    # use find_row_by_id function and tuple unpacking to find pet
    # in the 'pet_sheet'.
    pet_data, pet_row_index = find_row_by_id(pets_sheet, pet_id_str)

    if pet_row_index == -1:
        return  # check if find_row_by_id returned an error signal (-1).
    if not pet_data:
        # if not found, warn and exit function.
        print(f"Warning: Pet with ID {pet_id_str} not found.")
        return

    # Show pet data and inform user
    print("-" * 10)
    # show which pet was found.
    print(f"   Pet Found: {pet_data[1]} ({pet_data[3]}, Age: {pet_data[2]}"
          f" months) - ID #{pet_id_str}")
    # warn about removing the link too.
    print("   Warning: Deleting this pet will also clear its assignment "
          "in the 'Owners' sheet.")
    print("-" * 10)

    # Confirm Deletion
    delete_prompt = (f"Are you sure you want to delete Pet '{pet_data[1]}' "
                     f"(ID #{pet_id_str})?")
    # call confirm_action and proceed only if it returns True.
    if confirm_action(delete_prompt):
        try:  # try block for sheet modification (may fail).
            # delete from Pet sheet (delete_rows method, pass row index).
            pets_sheet.delete_rows(pet_row_index)
            print(f"   Deleted row {pet_row_index} from 'Pets' sheet.")

            # Find and delete from Owners sheet
            # search 'owners_sheet' for matching the pet's ID.
            owner_row, owner_row_index = find_row_by_pet_id(owners_sheet,
                                                            pet_id_str)

            # check if find_row_by_pet_id returned an error signal (-1).
            if owner_row_index == -1:
                # pet already deleted from the Pets sheet at this point.
                print("Warning: Could not check 'Owners' sheet due to an "
                      "error, but pet deleted from 'Pets'.")
            elif owner_row:
                # if owner_row exist, clear the Pet ID cell using update_cell
                # takes and "" value.
                owners_sheet.update_cell(owner_row_index, 2, "")
                print(f"   Cleared Pet ID link in 'Owners' sheet "
                      f"(Row {owner_row_index}).")
            else:
                # if owner_row not exist, inform that no deletion needed.
                print("   Info: No corresponding link found in "
                      "'Owners' sheet.")

            print("-" * 10)
            # show operation success message.
            print(f"Success: Pet '{pet_data[1]}' successfully deleted.")
            print("-" * 10)

        # Handle Errors during Sheet Access
        except gspread.exceptions.APIError as e:
            # if error related to the Google Sheets API
            print(f"Error: Google Sheets API Error deleting pet: {e}")
        except Exception as e:
            # any unexpected errors during the search.
            print(f"Error: An unexpected error occurred deleting pet: {e}")
    else:
        print("   Deletion cancelled.")


def exit_app():
    """Exits the application."""
    print("\nThank you for using Forever Home Friends!")
    # call sys.exit from imported 'sys' module for clean exit from the script.
    sys.exit()


# Main Application Loop
def main():
    """Runs the main application menu loop."""
    print("Welcome to Forever Home Friends!")

    # 'while True' loop runs until explicitly stopped by sys.exit,
    # keeps the menu displaying after each action.
    while True:
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

        # prompt the user and get input string removing whitespace.
        choice = input("Please enter your choice (1-8): ").strip()

        if choice == '1':  # if/elif/else structure to check the user's choice.
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
            # if the input doesn't match any choice
            print("Warning: Invalid choice. Please enter a number "
                  "between 1 and 8.")

        # pause so the the user can easily see the output.
        input("\nPress Enter to return to the main menu...")


# Run the application
# ensure that main function is called only when we run run.py directly
# from the command line.
if __name__ == "__main__":
    main()
