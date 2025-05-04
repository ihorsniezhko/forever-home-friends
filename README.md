# Forever Home Friends

Forever Home Friends is a Python command-line application designed to help manage a simple database of children and their adopted pet puppies and kittens. The application uses a Google Sheet ("forever_home_friends") to store and manage the data persistently, interacting directly with the Google Sheets API via the `gspread` library.

![Mockup showing the application running in a terminal](placeholder_terminal_mockup.png)

## Usage

The application provides a text-based menu interface for easy interaction. You will be presented with the main menu:

```
--- Main Menu ---
1. Add a Child
2. Add a Pet
3. Link Child and Pet
4. Search Pet by Child ID
5. Search Child by Pet ID
6. Delete a Child by ID
7. Delete a Pet by ID
8. Exit Application
-------------------------
Please enter your choice (1-8):
```

Follow the on-screen prompts to perform actions:
* Enter the corresponding number for the desired operation.
* When adding a pet type, enter 'p' for puppy or 'k' for kitty.
* When asked for confirmation, enter 'y' for yes or 'n' for no.
* After most actions, press Enter to return to the main menu.

The application includes input validation to guide the user and provides status messages (Success, Warning, Error, Info) for feedback.

## Features

* **Add Child:** Add a new child record (First Name, Last Name, Age 5-18) to the "Children" sheet. Assigns a unique sequential ID. Validates input and handles potential errors.
* **Add Pet:** Add a new pet record (Nickname, Age 0-12 months, Type) to the "Pets" sheet. Accepts 'p' or 'k' (case-insensitive) for pet type input but stores the full word "puppy" or "kitty". Assigns a unique sequential ID. Validates input and handles errors.
* **Link Child and Pet:** Create an association between an existing child and an existing pet using their IDs. Updates the "Owners" sheet.
    * Warns if the selected child already has a pet linked and asks for confirmation to replace the link.
    * Warns if the selected pet is already linked to another child (assigning it will remove the previous link).
    * Handles adding new entries or updating existing entries in the "Owners" sheet.
* **Search Pet by Child ID:** Find and display the details of the pet linked to a specific child ID by searching the "Owners" and "Pets" sheets. Handles cases where the child or pet is not found or not linked, including potential data inconsistencies.
* **Search Child by Pet ID:** Find and display the details of the child linked to a specific pet ID by searching the "Owners" and "Children" sheets. Handles cases where the pet or child is not found or not linked, including potential data inconsistencies.
* **Delete Child by ID:** Remove a child record from the "Children" sheet after confirmation ('y'/'n'). Also finds and removes the corresponding *entire row* from the "Owners" sheet.
* **Delete Pet by ID:** Remove a pet record from the "Pets" sheet after confirmation ('y'/'n'). Also finds the corresponding entry in the "Owners" sheet and *clears the Pet ID cell*, leaving the child entry intact but unlinked.
* **Data Persistence:** All data is stored in a Google Sheet, ensuring information is saved between application runs.
* **Input Validation:** Includes robust checks via helper functions for valid numeric input (integers), value ranges (ages), specific characters ('p'/'k'), non-empty input, and confirmation ('y'/'n').
* **User Feedback:** Provides clear status messages ("Success:", "Warning:", "Error:", "Info:") for operations and potential issues.
* **Error Handling:** Uses `try...except` blocks to gracefully handle potential errors during Google Sheet API interactions (e.g., `FileNotFoundError`, `SpreadsheetNotFound`, `WorksheetNotFound`, `APIError`) and provides informative messages.

## Data Storage

The application utilizes a Google Sheet named `forever_home_friends` for data storage. This sheet must contain three specific worksheets with the following columns (Header rows are recommended):

1.  **Children**
    * Column 1: `ID` (Integer, unique, auto-assigned sequentially)
    * Column 2: `First Name` (Text)
    * Column 3: `Last Name` (Text)
    * Column 4: `Age (Years)` (Integer, range 5-18)
2.  **Pets**
    * Column 1: `ID` (Integer, unique, auto-assigned sequentially)
    * Column 2: `Nickname` (Text)
    * Column 3: `Age (Months)` (Integer, range 0-12)
    * Column 4: `Pet` (Text: stored as "puppy" or "kitty")
3.  **Owners**
    * Column 1: `Child's name` (Text, format: "First Name Last Name" from Children sheet)
    * Column 2: `Pet Number` (Integer, the ID from the Pets sheet)

## Testing

Manual testing was performed extensively to cover all application features and potential user inputs.

**1. Add Child (Menu Option 1)**

* **Action:** Enter valid details (Name, Age within 5-18).
    * **Expected Outcome:** Child added to 'Children' sheet, Success message with new ID displayed.
* **Action:** Enter non-numeric age (e.g., "abc").
    * **Expected Outcome:** Warning message about invalid age, age prompt repeats.
* **Action:** Enter age outside range (e.g., 4 or 19).
    * **Expected Outcome:** Warning message about age range, age prompt repeats.
* **Action:** Enter empty first or last name.
    * **Expected Outcome:** Warning message about empty input, returns to relevant prompt or menu.

**2. Add Pet (Menu Option 2)**

* **Action:** Enter valid details (Nickname, Age 0-12, Type 'p' or 'k').
    * **Expected Outcome:** Pet added to 'Pets' sheet (storing full type "puppy"/"kitty"), Success message with new ID displayed.
* **Action:** Enter invalid pet type (e.g., 'd').
    * **Expected Outcome:** Warning message "enter 'p' or 'k'", type prompt repeats.
* **Action:** Enter non-numeric age (e.g., "xyz").
    * **Expected Outcome:** Warning message about invalid age, age prompt repeats.
* **Action:** Enter age outside range (e.g., -1 or 13).
    * **Expected Outcome:** Warning message about age range, age prompt repeats.
* **Action:** Enter empty nickname.
    * **Expected Outcome:** Warning message about empty input, returns to relevant prompt or menu.

**3. Link Child & Pet (Menu Option 3)**

* **Action:** Enter valid, existing, unlinked Child and Pet IDs, confirm 'y'.
    * **Expected Outcome:** Child/Pet details shown, final confirmation 'y', "Owners" sheet updated, Success message.
* **Action:** Enter non-existent Child ID.
    * **Expected Outcome:** Warning "Child with ID ... not found", ID prompt repeats.
* **Action:** Enter non-existent Pet ID (after valid Child ID).
    * **Expected Outcome:** Warning "Pet with ID ... not found", ID prompt repeats.
* **Action:** Enter valid IDs where the Child is already linked, confirm replacement ('y').
    * **Expected Outcome:** Warning about existing link shown, replace confirmation prompt shown, user enters 'y', final confirmation prompt shown, user enters 'y', link updated in "Owners", Success message.
* **Action:** Enter valid IDs where the Child is already linked, deny replacement ('n').
    * **Expected Outcome:** Warning about existing link shown, replace confirmation prompt shown, user enters 'n', "Operation cancelled." message shown, function exits.
* **Action:** Enter valid IDs where the Pet is already linked to another child, confirm 'y'.
    * **Expected Outcome:** Warning about pet already linked shown, final confirmation 'y', previous owner's link cleared, new link created/updated, Success message.
* **Action:** Cancel final confirmation ('n').
    * **Expected Outcome:** "Operation cancelled." message shown.

**4. Search Pet by Child ID (Menu Option 4)**

* **Action:** Enter ID of a child linked to a pet.
    * **Expected Outcome:** Success message showing details for both Child and linked Pet.
* **Action:** Enter ID of a child not linked to any pet.
    * **Expected Outcome:** Info message stating the child is not currently linked.
* **Action:** Enter non-existent Child ID.
    * **Expected Outcome:** Warning "Child with ID ... not found".
* **Action:** Test data inconsistency (Child linked in "Owners", but Pet deleted from "Pets").
    * **Expected Outcome:** Warning message about missing pet data after finding the link.

**5. Search Child by Pet ID (Menu Option 5)**

* **Action:** Enter ID of a pet linked to a child.
    * **Expected Outcome:** Success message showing details for both Pet and linked Child.
* **Action:** Enter ID of a pet not linked to any child.
    * **Expected Outcome:** Info message stating the pet is not currently linked.
* **Action:** Enter non-existent Pet ID.
    * **Expected Outcome:** Warning "Pet with ID ... not found".
* **Action:** Test data inconsistency (Pet linked in "Owners", but Child deleted from "Children").
    * **Expected Outcome:** Warning message about missing child data after finding the link.

**6. Delete Child by ID (Menu Option 6)**

* **Action:** Enter ID of an existing child, confirm 'y'.
    * **Expected Outcome:** Child details shown, confirmation 'y', row deleted from "Children", corresponding row deleted from "Owners", Success message.
* **Action:** Enter non-existent Child ID.
    * **Expected Outcome:** Warning "Child with ID ... not found".
* **Action:** Enter valid Child ID, cancel deletion ('n').
    * **Expected Outcome:** "Deletion cancelled." message shown, data remains unchanged.
* **Action:** Delete child who had no link in "Owners".
    * **Expected Outcome:** Child deleted from "Children", Info message "No corresponding entry found in 'Owners' sheet", overall Success message.

**7. Delete Pet by ID (Menu Option 7)**

* **Action:** Enter ID of an existing linked pet, confirm 'y'.
    * **Expected Outcome:** Pet details shown, confirmation 'y', row deleted from "Pets", Pet ID cell cleared in "Owners", Success message.
* **Action:** Enter non-existent Pet ID.
    * **Expected Outcome:** Warning "Pet with ID ... not found".
* **Action:** Enter valid Pet ID, cancel deletion ('n').
    * **Expected Outcome:** "Deletion cancelled." message shown, data remains unchanged.
* **Action:** Delete pet who had no link in "Owners".
    * **Expected Outcome:** Pet deleted from "Pets", Info message "No corresponding link found in 'Owners' sheet", overall Success message.

**8. Exit Application (Menu Option 8)**

* **Action:** Select option 8.
    * **Expected Outcome:** Goodbye message displayed, application terminates cleanly.

**9. General Testing**

* **Action:** Run application with initially empty Google Sheets (except headers).
    * **Expected Outcome:** `get_next_id` correctly returns 1, add functions work, search/delete functions handle empty data gracefully (e.g., "not found" messages).
* **Action:** Test non-numeric input where IDs are expected.
    * **Expected Outcome:** Warning message about invalid ID, prompt repeats.
* **Action:** Test empty input at various prompts.
    * **Expected Outcome:** Warning "Input cannot be empty", prompt repeats.

### Validator Testing

* The Python code (`run.py`) was checked using the Flake8 linter (`flake8 run.py`). No major PEP8 violations or logical errors were reported.

## Known Issues

* **Single Pet per Child:** The current version only allows one pet to be linked to one child. Attempting to link a second pet will overwrite the first link after confirmation.
* **Name Uniqueness Assumption:** The application relies on child names (First + Last) being unique when searching the "Owners" sheet (`find_row_by_child_name`) and when looking up child details based on a name from the "Owners" sheet (`search_by_pet`). Duplicate child names could lead to unexpected behavior (e.g., finding the wrong child's link, or `search_by_pet` finding the first matching name in the Children sheet).
* **Limited Search:** Search functionality is currently limited to lookup by ID.

## Future Enhancements

* Allowing a child to be linked to multiple pets (would require changing the "Owners" sheet structure).
* Using Child ID instead of Child Name in the "Owners" sheet to avoid ambiguity with duplicate names.
* Adding search functionality based on other criteria (e.g., pet type, child age, child name).
* Implementing data sorting or viewing options.
* Developing a graphical user interface (GUI).

## Technologies Used

* [Python 3](https://www.python.org/) - Version 3.13.1.
* [gspread](https://github.com/burnash/gspread) Python library - For interacting with Google Sheets.
* [google-auth & google-auth-oauthlib](https://github.com/googleapis/google-auth-library-python) - For handling Google API authentication (`Credentials` class).
* [Google Sheets API](https://developers.google.com/sheets/api)
* [Google Drive API](https://developers.google.com/drive/api/v3/about-sdk)
* [Google Cloud Platform (GCP)](https://cloud.google.com/) - For Service Account credentials.
* [Node.js](https://nodejs.org/) - Used by the Heroku deployment template for the web terminal interface.