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
        And a customer exists with ID "12345" and status "inactive"
        When I click the "Activate" button for customer "12345"
        Then I should see "Success: Customer activated!"
        And I should see the status for customer "12345" change to "active"

    Scenario: Deactivate a customer account
        Given I am on the home page
        And a customer exists with ID "12345" and status "active"
        When I click the "Deactivate" button for customer "12345"
        Then I should see "Success: Customer deactivated!"
        And I should see the status for customer "12345" change to "inactive"

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
