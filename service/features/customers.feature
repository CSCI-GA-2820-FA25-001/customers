Feature: Customer Actions UI
    As an eCommerce manager
    I need to perform actions on customer accounts
    So that I can manage customer status from the UI

    Background:
        Given the customer service is running
        And I am on the home page

    Scenario: The UI is accessible
        When I visit the home page
        Then the page should load successfully

    Scenario: Activate a customer account
        Given a customer exists with ID "12345" and status "inactive"
        When I click the "Activate" button for customer "12345"
        Then I should see "Success: Customer activated!"
        And I should see the status for customer "12345" change to "active"

    Scenario: Deactivate a customer account
        Given a customer exists with ID "12345" and status "active"
        When I click the "Deactivate" button for customer "12345"
        Then I should see "Success: Customer deactivated!"
        And I should see the status for customer "12345" change to "inactive"

    Scenario: Suspend a customer account
        Given a customer exists with ID "12345" and status "active"
        When I click the "Suspend" button for customer "12345"
        Then I should see "Success: Customer suspended!"
        And I should see the status for customer "12345" change to "suspended"

    Scenario: Attempt to activate a non-existing customer
        Given no customer exists with ID "99999"
        When I click the "Activate" button for customer "99999"
        Then I should see "Error: Customer not found"
