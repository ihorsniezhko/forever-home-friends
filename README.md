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

---

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

---

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

---

## Deployment
