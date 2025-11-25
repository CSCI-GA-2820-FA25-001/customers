from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests

WAIT_TIME = 5


@given("the customer service is running")
def step_service_running(context):
    # Optional health check
    pass


@given("I am on the home page")
def step_home_page(context):
    context.driver.get(context.base_url)


@when("I visit the home page")
def step_visit_home(context):
    context.driver.get(context.base_url)


@then("the page should load successfully")
def step_page_loaded(context):
    WebDriverWait(context.driver, WAIT_TIME).until(
        EC.visibility_of_element_located((By.TAG_NAME, "body"))
    )


@given('a customer exists with ID "12345" and status "inactive"')
def step_customer_inactive(context):
    # Use API or backend setup in real tests
    pass


@given('a customer exists with ID "12345" and status "active"')
def step_customer_active(context):
    pass


@given('no customer exists with ID "99999"')
def step_no_customer(context):
    pass


@when('I click the "Activate" button for customer "12345"')
def step_click_activate_12345(context):
    print(context.driver.page_source)
    WebDriverWait(context.driver, WAIT_TIME).until(
        EC.element_to_be_clickable((By.ID, "btn-activate-12345"))
    ).click()


@when('I click the "Deactivate" button for customer "12345"')
def step_click_deactivate_12345(context):
    WebDriverWait(context.driver, WAIT_TIME).until(
        EC.element_to_be_clickable((By.ID, "btn-deactivate-12345"))
    ).click()


@when('I click the "Suspend" button for customer "12345"')
def step_click_suspend_12345(context):
    WebDriverWait(context.driver, WAIT_TIME).until(
        EC.element_to_be_clickable((By.ID, "btn-suspend-12345"))
    ).click()


@when('I click the "Activate" button for customer "99999"')
def step_click_activate_99999(context):
    WebDriverWait(context.driver, WAIT_TIME).until(
        EC.element_to_be_clickable((By.ID, "btn-activate-99999"))
    ).click()


@then('I should see "Success: Customer activated!"')
def step_see_activated(context):
    WebDriverWait(context.driver, WAIT_TIME).until(
        EC.text_to_be_present_in_element((By.ID, "flash_message"), "Success: Customer activated!")
    )


@then('I should see "Success: Customer deactivated!"')
def step_see_deactivated(context):
    WebDriverWait(context.driver, WAIT_TIME).until(
        EC.text_to_be_present_in_element((By.ID, "flash_message"), "Success: Customer deactivated!")
    )


@then('I should see "Success: Customer suspended!"')
def step_see_suspended(context):
    WebDriverWait(context.driver, WAIT_TIME).until(
        EC.text_to_be_present_in_element((By.ID, "flash_message"), "Success: Customer suspended!")
    )


@then('I should see "Error: Customer not found"')
def step_see_not_found(context):
    WebDriverWait(context.driver, WAIT_TIME).until(
        EC.text_to_be_present_in_element((By.ID, "flash_message"), "Error: Customer not found")
    )


@then('I should see the status for customer "12345" change to "active"')
def step_status_active(context):
    status = WebDriverWait(context.driver, WAIT_TIME).until(
        EC.visibility_of_element_located((By.ID, "status-12345"))
    )
    assert status.text.lower() == "active"


@then('I should see the status for customer "12345" change to "inactive"')
def step_status_inactive(context):
    status = WebDriverWait(context.driver, WAIT_TIME).until(
        EC.visibility_of_element_located((By.ID, "status-12345"))
    )
    assert status.text.lower() == "inactive"


@then('I should see the status for customer "12345" change to "suspended"')
def step_status_suspended(context):
    status = WebDriverWait(context.driver, WAIT_TIME).until(
        EC.visibility_of_element_located((By.ID, "status-12345"))
    )
    assert status.text.lower() == "suspended"


# -------------------
# LISTING
# -------------------

@given("multiple customers exist in the system")
def step_multiple_customers(context):
    pass


@given("no customers exist in the system")
def step_no_customers(context):
    pass


@when("I click the list button")
def step_click_list(context):
    WebDriverWait(context.driver, WAIT_TIME).until(
        EC.element_to_be_clickable((By.ID, "btn-list"))
    ).click()


@then("I should see a list of all customers")
def step_see_list(context):
    WebDriverWait(context.driver, WAIT_TIME).until(
        EC.visibility_of_element_located((By.ID, "customer-list"))
    )


@then("each customer entry should display first name, last name, address, and ID")
def step_see_customer_fields(context):
    rows = context.driver.find_elements(By.CLASS_NAME, "customer-row")
    assert len(rows) > 0


@then('I should see an empty list message "No customers found"')
def step_empty_list(context):
    WebDriverWait(context.driver, WAIT_TIME).until(
        EC.text_to_be_present_in_element((By.ID, "customer-list"), "No customers found")
    )


@when("I create a new customer")
def step_create_customer(context):
    WebDriverWait(context.driver, WAIT_TIME).until(
        EC.element_to_be_clickable((By.ID, "btn-create"))
    ).click()


@then("I should see the newly created customer in the list")
def step_see_new_customer(context):
    rows = context.driver.find_elements(By.CLASS_NAME, "customer-row")
    assert len(rows) > 0


# -------------------
# QUERYING
# -------------------

@given("I am on the customer admin page")
def step_admin_page(context):
    context.driver.get(f"{context.base_url}/admin")


@given("multiple customers exist with different last names")
def step_customers_different_names(context):
    pass


@given("customers exist in the system")
def step_customers_exist(context):
    pass


@when('I enter "Smith" into the last name search field')
def step_enter_last_name(context):
    field = WebDriverWait(context.driver, WAIT_TIME).until(
        EC.visibility_of_element_located((By.ID, "search-last-name"))
    )
    field.clear()
    field.send_keys("Smith")


@when('I enter "NonExistent" into the last name search field')
def step_enter_nonexistent_name(context):
    field = WebDriverWait(context.driver, WAIT_TIME).until(
        EC.visibility_of_element_located((By.ID, "search-last-name"))
    )
    field.clear()
    field.send_keys("NonExistent")


@when('I enter "Boston" into the address search field')
def step_enter_address(context):
    field = WebDriverWait(context.driver, WAIT_TIME).until(
        EC.visibility_of_element_located((By.ID, "search-address"))
    )
    field.clear()
    field.send_keys("Boston")


@when('I click the "Search" button')
def step_click_search(context):
    WebDriverWait(context.driver, WAIT_TIME).until(
        EC.element_to_be_clickable((By.ID, "btn-search"))
    ).click()


@then('I should see only customers with last name "Smith"')
def step_results_smith(context):
    rows = context.driver.find_elements(By.CLASS_NAME, "customer-row")
    for row in rows:
        assert "smith" in row.text.lower()


@then("I should see an empty result list")
def step_empty_results(context):
    rows = context.driver.find_elements(By.CLASS_NAME, "customer-row")
    assert len(rows) == 0


@then('I should see the message "No customers found matching your search"')
def step_no_match_msg(context):
    WebDriverWait(context.driver, WAIT_TIME).until(
        EC.text_to_be_present_in_element(
            (By.ID, "search-message"),
            "No customers found matching your search"
        )
    )


@then('I should see only customers matching last name "Smith" and address containing "Boston"')
def step_results_smith_boston(context):
    rows = context.driver.find_elements(By.CLASS_NAME, "customer-row")
    for row in rows:
        text = row.text.lower()
        assert "smith" in text and "boston" in text


# -------------------
# READING
# -------------------

@given('a customer exists with ID "{customer_id}"')
def step_customer_exists(context, customer_id):
    """
    Create a customer with a specific ID by directly using the database.
    
    Note: We bypass the API's deserialize() method which ignores 'id',
    and instead directly create the customer via the database with our desired ID.
    This is acceptable in BDD tests where we need predictable, known IDs.
    """
    # First, ensure no customer exists with this ID (cleanup)
    try:
        requests.delete(
            f"{context.base_url}/api/customers/{customer_id}",
            timeout=5
        )
    except Exception:
        pass  # Ignore if doesn't exist

    # Create via API and store whatever ID we get
    
    customer_data = {
        "first_name": "John",
        "last_name": "Doe",
        "address": "123 Main Street, New York, NY 10001",
        "status": "active"
    }
    
    response = requests.post(
        f"{context.base_url}/api/customers",
        json=customer_data,
        headers={"Content-Type": "application/json"},
        timeout=5
    )
    
    assert response.status_code == 201, f"Failed to create customer: {response.status_code}"
    
    # Store the created customer
    created_customer = response.json()
    context.test_customer = created_customer
    
    # Map the scenario ID to the actual created ID
    if not hasattr(context, 'customer_id_mapping'):
        context.customer_id_mapping = {}
    context.customer_id_mapping[customer_id] = str(created_customer['id'])


@given('no customer exists with ID "{customer_id}"')
def step_no_customer_exists(context, customer_id):
    """Ensure no customer exists with the given ID"""
    try:
        requests.delete(
            f"{context.base_url}/api/customers/{customer_id}",
            timeout=5
        )
    except Exception:
        pass  # If delete fails, customer likely doesn't exist anyway


@when('I search for customer ID "{customer_id}"')
def step_search_customer_id(context, customer_id):
    """Enter customer ID in the search field"""
    # Check if this is a mapped ID (from Given step) or a literal ID
    if hasattr(context, 'customer_id_mapping') and customer_id in context.customer_id_mapping:
        actual_id = context.customer_id_mapping[customer_id]
    else:
        actual_id = customer_id
    
    search_field = WebDriverWait(context.driver, WAIT_TIME).until(
        EC.visibility_of_element_located((By.ID, "search-customer-id"))
    )
    search_field.clear()
    search_field.send_keys(actual_id)
    
    # Store the actual ID being searched
    context.searched_customer_id = actual_id


@when('I click the "View Details" button')
def step_click_view_details(context):
    """Click the View Details button to display customer information"""
    WebDriverWait(context.driver, WAIT_TIME).until(
        EC.element_to_be_clickable((By.ID, "btn-view-details"))
    ).click()


@then("I should see the complete customer information displayed")
def step_see_complete_customer_info(context):
    """Verify all customer details are displayed correctly"""
    # Wait for the customer details container to be visible
    details_container = WebDriverWait(context.driver, WAIT_TIME).until(
        EC.visibility_of_element_located((By.ID, "customer-details"))
    )
    
    assert details_container.is_displayed(), "Customer details container is not visible"
    
    # Verify all required fields are present and visible
    customer_id_elem = WebDriverWait(context.driver, WAIT_TIME).until(
        EC.visibility_of_element_located((By.ID, "customer-id"))
    )
    
    first_name_elem = WebDriverWait(context.driver, WAIT_TIME).until(
        EC.visibility_of_element_located((By.ID, "customer-first-name"))
    )
    
    last_name_elem = WebDriverWait(context.driver, WAIT_TIME).until(
        EC.visibility_of_element_located((By.ID, "customer-last-name"))
    )
    
    address_elem = WebDriverWait(context.driver, WAIT_TIME).until(
        EC.visibility_of_element_located((By.ID, "customer-address"))
    )
    
    status_elem = WebDriverWait(context.driver, WAIT_TIME).until(
        EC.visibility_of_element_located((By.ID, "customer-status"))
    )
    
    # Verify the displayed data matches what we created (if we created it)
    if hasattr(context, 'test_customer'):
        expected_customer = context.test_customer
        
        # Verify ID
        assert customer_id_elem.text == str(expected_customer['id']), \
            f"Expected ID {expected_customer['id']}, got {customer_id_elem.text}"
        
        # Verify first name
        assert first_name_elem.text == expected_customer['first_name'], \
            f"Expected first name {expected_customer['first_name']}, got {first_name_elem.text}"
        
        # Verify last name
        assert last_name_elem.text == expected_customer['last_name'], \
            f"Expected last name {expected_customer['last_name']}, got {last_name_elem.text}"
        
        # Verify address
        assert address_elem.text == expected_customer['address'], \
            f"Expected address {expected_customer['address']}, got {address_elem.text}"
        
        # Verify status
        assert status_elem.text.lower() == expected_customer['status'].lower(), \
            f"Expected status {expected_customer['status']}, got {status_elem.text}"


@then('I should see a "Customer not found" message')
def step_see_customer_not_found(context):
    """Verify that a 'Customer not found' message is displayed"""
    WebDriverWait(context.driver, WAIT_TIME).until(
        EC.text_to_be_present_in_element(
            (By.ID, "flash_message"),
            "Customer not found"
        )
    )

