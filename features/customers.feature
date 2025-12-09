Feature: Customer User Interface
    As an eCommerce manager or developer
    I want a unified UI for managing and querying customers
    So that I can perform actions, listings, and queries from one interface

    Background:
        Given the customer service is running
        And I am on the home page

    # ------------------------
    # ACTIONS (Status Changes)
    # ------------------------

    Scenario: The UI is accessible
        When I visit the home page
        Then the page should load successfully

    Scenario: Activate a customer account
        Given the following customers exist:
            | first_name | last_name | address         | status      |
            | Alice      | Wonder    | 100 Fantasy Ln  | deactivated |
        When I click the "List All Customers" button
        And I click the "Activate" button for customer "Alice Wonder"
        Then I should see the message "Success"
        And I should see the status change to "active" for customer "Alice Wonder"

    Scenario: Deactivate a customer account
        Given the following customers exist:
            | first_name | last_name | address        | status |
            | Bob        | Builder   | 200 Construct  | active |
        When I click the "List All Customers" button
        And I click the "Deactivate" button for customer "Bob Builder"
        Then I should see the message "Success"
        And I should see the status change to "deactivated" for customer "Bob Builder"

    Scenario: Suspend a customer account
        Given the following customers exist:
            | first_name | last_name | address       | status |
            | Charlie    | Chaplin   | 300 Silent St | active |
        When I click the "List All Customers" button
        And I click the "Suspend" button for customer "Charlie Chaplin"
        Then I should see the message "Success"
        And I should see the status change to "suspended" for customer "Charlie Chaplin"

    # ------------------------
    # CREATE
    # ------------------------

    Scenario: Create a new customer
        When I set the "First Name" to "David"
        And I set the "Last Name" to "Davidson"
        And I set the "Address" to "400 New Ave"
        And I click the "Create" button
        Then I should see the message "Success"
        When I click the "List All Customers" button
        Then I should see "David" in the results
        And I should see "Davidson" in the results
        And I should see "400 New Ave" in the results

    Scenario: Create a customer with missing first name
        When I set the "Last Name" to "NoFirst"
        And I set the "Address" to "500 Missing St"
        And I click the "Create" button
        Then I should see the message "first_name is required"

    Scenario: Create a customer with missing last name
        When I set the "First Name" to "NoLast"
        And I set the "Address" to "600 Missing Ave"
        And I click the "Create" button
        Then I should see the message "last_name is required"

    Scenario: Create a customer with missing address
        When I set the "First Name" to "NoAddr"
        And I set the "Last Name" to "Person"
        And I click the "Create" button
        Then I should see the message "address is required"

    # ------------------------
    # LISTING
    # ------------------------

    Scenario: List all customers
        Given the following customers exist:
            | first_name | last_name | address         |
            | Eve        | Evans     | 700 Garden Rd   |
            | Frank      | Fisher    | 800 Ocean Blvd  |
            | Grace      | Green     | 900 Forest Way  |
        When I click the "List All Customers" button
        Then I should see "Eve" in the results
        And I should see "Frank" in the results
        And I should see "Grace" in the results

    Scenario: List when no customers exist
        Given there are no customers
        When I click the "List All Customers" button
        Then I should see the message "No customers found"

    # ------------------------
    # QUERYING / SEARCH
    # ------------------------

    Scenario: Search customers by last name
        Given the following customers exist:
            | first_name | last_name | address         |
            | Henry      | Hill      | 1000 Mountain   |
            | Ivy        | Hill      | 1100 Valley     |
            | Jack       | Jones     | 1200 Plains     |
        When I set the "Search Last Name" to "Hill"
        And I click the "Search" button
        Then I should see "Henry" in the results
        And I should see "Ivy" in the results
        And I should not see "Jack" in the results

    Scenario: Search with no matching results
        Given the following customers exist:
            | first_name | last_name | address       |
            | Kate       | King      | 1300 Castle   |
        When I set the "Search Last Name" to "NonExistent"
        And I click the "Search" button
        Then I should see the message "No customers found"

    Scenario: Search by address
        Given the following customers exist:
            | first_name | last_name | address         |
            | Leo        | Lewis     | 1400 Boston Ave |
            | Mia        | Moore     | 1500 Boston Rd  |
            | Nick       | Nelson    | 1600 Chicago St |
        When I set the "Search Address" to "Boston"
        And I click the "Search" button
        Then I should see "Leo" in the results
        And I should see "Mia" in the results
        And I should not see "Nick" in the results

    # ------------------------
    # READ (View Details)
    # ------------------------

    Scenario: Read an existing customer
        Given the following customers exist:
            | first_name | last_name | address        |
            | Olivia     | Owen      | 1700 Park Ave  |
        When I click the "List All Customers" button
        And I click the "Edit" button for customer "Olivia Owen"
        Then the "First Name" field should contain "Olivia"
        And the "Last Name" field should contain "Owen"
        And the "Address" field should contain "1700 Park Ave"

    # ------------------------
    # UPDATE
    # ------------------------

    Scenario: Update an existing customer
        Given the following customers exist:
            | first_name | last_name | address         |
            | Paul       | Parker    | 1800 Old Street |
        When I click the "List All Customers" button
        And I click the "Edit" button for customer "Paul Parker"
        And I set the "Address" to "1900 New Street"
        And I click the "Update" button
        Then I should see the message "Success"
        When I click the "List All Customers" button
        Then I should see "1900 New Street" in the results

    Scenario: Update with invalid data (empty first name)
        Given the following customers exist:
            | first_name | last_name | address        |
            | Quinn      | Quest     | 2000 Quest Rd  |
        When I click the "List All Customers" button
        And I click the "Edit" button for customer "Quinn Quest"
        And I clear the "First Name" field
        And I click the "Update" button
        Then I should see the message "first_name is required"

    # ------------------------
    # DELETE
    # ------------------------

    Scenario: Delete an existing customer
        Given the following customers exist:
            | first_name | last_name | address        |
            | Rachel     | Ross      | 2100 Delete St |
        When I click the "List All Customers" button
        And I click the "Delete" button for customer "Rachel Ross"
        And I confirm the deletion
        Then I should see the message "Success"
        When I click the "List All Customers" button
        Then I should not see "Rachel" in the results

    Scenario: Cancel customer deletion
        Given the following customers exist:
            | first_name | last_name | address        |
            | Sam        | Smith     | 2200 Keep Ave  |
        When I click the "List All Customers" button
        And I click the "Delete" button for customer "Sam Smith"
        And I cancel the deletion
        When I click the "List All Customers" button
        Then I should see "Sam" in the results
