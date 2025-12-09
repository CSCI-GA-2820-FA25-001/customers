Feature: The customer service back-end
    As a Customer Service Manager
    I need a RESTful catalog service
    So that I can keep track of all my customers

Background:
    Given the following customers
        | first_name | last_name | address          |
        | Alice      | Anderson  | 100 Main St      |
        | Bob        | Brown     | 200 Oak Ave      |
        | Charlie    | Chen      | 300 Pine Rd      |
        | Diana      | Davis     | 400 Elm Street   |

Scenario: The server is running
    When I visit the "Home Page"
    Then I should see "Customer" in the title
    And I should not see "404 Not Found"

Scenario: Create a Customer
    When I visit the "Home Page"
    And I set the "First Name" to "Emma"
    And I set the "Last Name" to "Evans"
    And I set the "Address" to "500 Maple Drive"
    And I press the "Create" button
    Then I should see the message "Success"
    When I press the "List All" button
    Then I should see the message "Success"
    And I should see "Emma" in the results
    And I should see "Evans" in the results
    And I should see "500 Maple Drive" in the results

Scenario: List all customers
    When I visit the "Home Page"
    And I press the "List All" button
    Then I should see the message "Success"
    And I should see "Alice" in the results
    And I should see "Bob" in the results
    And I should see "Charlie" in the results
    And I should see "Diana" in the results

Scenario: Search for customers by last name
    When I visit the "Home Page"
    And I set the "Search Last Name" to "Brown"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "Bob" in the results
    And I should not see "Alice" in the results
    And I should not see "Charlie" in the results

Scenario: Search by address
    When I visit the "Home Page"
    And I set the "Search Address" to "Pine"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "Charlie" in the results
    And I should not see "Alice" in the results
    And I should not see "Bob" in the results

Scenario: Search for customer by ID
    When I visit the "Home Page"
    And I press the "List All" button
    Then I should see the message "Success"
    And I should see "Alice" in the results

Scenario: Clear the form
    When I visit the "Home Page"
    And I set the "First Name" to "Test"
    And I set the "Last Name" to "User"
    And I set the "Address" to "123 Test St"
    And I press the "Clear" button
    Then the "First Name" field should be empty
    And the "Last Name" field should be empty
    And the "Address" field should be empty

# ------------------------------------------------------------------
# UPDATE Scenario
# ------------------------------------------------------------------

Scenario: Update a Customer
    When I visit the "Home Page"
    And I press the "List All" button
    Then I should see the message "Success"
    And I should see "Alice" in the results
    When I press the "Edit" button for customer "Alice Anderson"
    And I change "First Name" to "Alicia"
    And I press the "Update" button
    Then I should see the message "Success"
    When I press the "List All" button
    Then I should see the message "Success"
    And I should see "Alicia" in the results

# ------------------------------------------------------------------
# DELETE Scenarios
# ------------------------------------------------------------------

Scenario: Delete a Customer
    When I visit the "Home Page"
    And I press the "List All" button
    Then I should see the message "Success"
    And I should see "Diana" in the results
    When I press the "Delete" button for customer "Diana Davis"
    And I confirm the deletion
    Then I should see the message "Success"
    When I press the "List All" button
    Then I should see the message "Success"
    And I should not see "Diana" in the results

Scenario: Cancel deleting a Customer
    When I visit the "Home Page"
    And I press the "List All" button
    Then I should see the message "Success"
    And I should see "Bob" in the results
    When I press the "Delete" button for customer "Bob Brown"
    And I cancel the deletion
    When I press the "List All" button
    Then I should see the message "Success"
    And I should see "Bob" in the results

# ------------------------------------------------------------------
# STATUS ACTION Scenarios (Activate, Deactivate, Suspend)
# ------------------------------------------------------------------

Scenario: Suspend an active Customer
    When I visit the "Home Page"
    And I press the "List All" button
    Then I should see the message "Success"
    And I should see "Bob" in the results
    When I press the "Suspend" button for customer "Bob Brown"
    Then I should see the message "Success"
    When I press the "List All" button
    Then I should see the message "Success"
    And I should see "suspended" as the status for "Bob Brown" in the results
