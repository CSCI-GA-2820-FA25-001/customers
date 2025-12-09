Feature: Customer User Interface
    As an eCommerce manager or developer
    I want a unified UI for managing and querying customers
    So that I can perform actions, listings, and queries from one interface

    Background:
        Given the customer service is running

    # ------------------------
    # ACTIONS
    # ------------------------

    Scenario: The UI is accessible
        Given I am on the home page
        When I visit the home page
        Then the page should load successfully

    Scenario: Activate a customer account
        Given I am on the home page
        And a customer exists with ID "12345" and status "deactivated"
        When I click the "Activate" button for customer "12345"
        Then I should see "Success: Customer activated!"
        And I should see the status for customer "12345" change to "active"

    Scenario: Deactivate a customer account
        Given I am on the home page
        And a customer exists with ID "12345" and status "active"
        When I click the "Deactivate" button for customer "12345"
        Then I should see "Success: Customer deactivated!"
        And I should see the status for customer "12345" change to "deactivated"

    Scenario: Suspend a customer account
        Given I am on the home page
        And a customer exists with ID "12345" and status "active"
        When I click the "Suspend" button for customer "12345"
        Then I should see "Success: Customer suspended!"
        And I should see the status for customer "12345" change to "suspended"

    Scenario: Attempt to activate a non-existing customer
        Given I am on the home page
        And no customer exists with ID "99999"
        When I click the "Activate" button for customer "99999"
        Then I should see "Error: Customer not found"

    # ------------------------
    # CREATE
    # ------------------------

    Scenario: Create a new customer
        Given I am on the home page
        When I fill in the customer form with valid data
        And I click the "Create Customer" button
        Then I should see a success message
        And the new customer should appear in the customer list

    Scenario: Create a customer with missing required fields
        Given I am on the home page
        When I fill in the customer form with incomplete data
        And I click the "Create Customer" button
        Then I should see an error message indicating which fields are required

    Scenario: Create a customer with empty first name
        Given I am on the home page
        When I leave the first name field empty
        And I fill in last name with "Smith"
        And I fill in address with "123 Main St"
        And I click the "Create Customer" button
        Then I should see an error message "first_name is required"

    Scenario: Create a customer with empty last name
        Given I am on the home page
        When I fill in first name with "John"
        And I leave the last name field empty
        And I fill in address with "123 Main St"
        And I click the "Create Customer" button
        Then I should see an error message "last_name is required"

    Scenario: Create a customer with empty address
        Given I am on the home page
        When I fill in first name with "John"
        And I fill in last name with "Smith"
        And I leave the address field empty
        And I click the "Create Customer" button
        Then I should see an error message "address is required"

    # ------------------------
    # LISTING
    # ------------------------

    Scenario: List all customers
        Given I am on the home page
        And multiple customers exist in the system
        When I click the list button
        Then I should see a list of all customers
        And each customer entry should display first name, last name, address, and ID

    Scenario: List when no customers exist
        Given I am on the home page
        And no customers exist in the system
        When I click the list button
        Then I should see an empty list message "No customers found"

    Scenario: List updates after creating a customer
        Given I am on the home page
        When I create a new customer
        And I click the list button
        Then I should see the newly created customer in the list

    # ------------------------
    # QUERYING
    # ------------------------

    Scenario: Query customers by last name
        Given I am on the customer admin page
        And multiple customers exist with different last names
        When I enter "Smith" into the last name search field
        And I click the "Search" button
        Then I should see only customers with last name "Smith"

    Scenario: Query with no matching results
        Given I am on the customer admin page
        And customers exist in the system
        When I enter "NonExistent" into the last name search field
        And I click the "Search" button
        Then I should see an empty result list
        And I should see the message "No customers found matching your search"

    Scenario: Query with multiple criteria
        Given I am on the customer admin page
        And multiple customers exist in the system
        When I enter "Smith" into the last name search field
        And I enter "Boston" into the address search field
        And I click the "Search" button
        Then I should see only customers matching last name "Smith" and address containing "Boston"

    # ------------------------
    # READING
    # ------------------------

    Scenario: Read an existing customer
        Given I am on the home page
        And a customer exists with ID "12345"
        When I search for customer ID "12345"
        And I click the "View Details" button
        Then I should see the complete customer information displayed

    Scenario: Read a non-existing customer
        Given I am on the home page
        And no customer exists with ID "99999"
        When I search for customer ID "99999"
        Then I should see a "Customer not found" message

    # ------------------------
    # DELETE
    # ------------------------

    Scenario: Delete an existing customer
        Given I am on the home page
        And a customer exists with ID "12345"
        When I click the "Delete" button for customer "12345"
        And I confirm the deletion
        Then I should see a success message
        #And the customer should no longer appear in the list

    Scenario: Cancel customer deletion
        Given I am on the home page
        And a customer exists with ID "12345"
        When I click the "Delete" button for customer "12345"
        And I cancel the deletion
        Then the customer should still appear in the list

    # ------------------------
    # UPDATE
    # ------------------------

    Scenario: Update an existing customer
        Given I am on the home page
        And a customer exists with ID "12345"
        When I navigate to edit customer "12345"
        And I update the customer's address to "123 New Street"
        And I click the "Update" button
        Then I should see a success message
        And the customer's address should be updated in the list

    Scenario: Update with invalid data
        Given I am on the home page
        And a customer exists with ID "12345"
        When I navigate to edit customer "12345"
        And I clear the required field "firstName"
        And I click the "Update" button
        Then I should see an error message about invalid data
