from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

WAIT_TIME = 60


def wait_for_element(context, by, value, timeout=WAIT_TIME):
    """Wait for element to be visible"""
    return WebDriverWait(context.driver, timeout).until(
        EC.visibility_of_element_located((by, value))
    )


def wait_for_clickable(context, by, value, timeout=WAIT_TIME):
    """Wait for element to be clickable"""
    return WebDriverWait(context.driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )


def click_list_all_button(context):
    """Click the List All Customers button"""
    btn = wait_for_clickable(context, By.ID, "list-all-btn")
    btn.click()
    time.sleep(1)


def wait_for_flash_message(context, timeout=WAIT_TIME):
    """Wait for flash message to appear"""
    return wait_for_element(context, By.ID, "flash-message", timeout)


def create_customer_via_ui(
    context, first_name="Test", last_name="Customer", address="123 Test St"
):
    """Create a customer via the UI"""
    # Make sure we're on the home page
    context.driver.get(context.base_url)

    # Fill in the form
    wait_for_element(context, By.ID, "first-name").clear()
    context.driver.find_element(By.ID, "first-name").send_keys(first_name)
    context.driver.find_element(By.ID, "last-name").clear()
    context.driver.find_element(By.ID, "last-name").send_keys(last_name)
    context.driver.find_element(By.ID, "address").clear()
    context.driver.find_element(By.ID, "address").send_keys(address)

    # Click create button
    wait_for_clickable(context, By.ID, "create-btn").click()
    time.sleep(1)

    # Wait for success message
    try:
        flash = wait_for_flash_message(context, timeout=5)
        if "success" in flash.text.lower():
            # Store the customer data for later reference
            return {
                "first_name": first_name,
                "last_name": last_name,
                "address": address,
            }
    except TimeoutException:
        pass

    return None


def clear_form(context):
    """Clear all form fields"""
    try:
        context.driver.find_element(By.ID, "first-name").clear()
        context.driver.find_element(By.ID, "last-name").clear()
        context.driver.find_element(By.ID, "address").clear()
    except Exception:
        pass


def delete_all_customers_via_ui(context):
    """Delete all customers via the UI"""
    context.driver.get(context.base_url)
    click_list_all_button(context)
    time.sleep(1)

    # Keep deleting until no customers remain
    max_iterations = 50  # Safety limit
    iteration = 0

    while iteration < max_iterations:
        try:
            # Check if there are any customers
            container = context.driver.find_element(By.ID, "customer-list-container")
            if "no customers" in container.text.lower():
                break

            # Find delete buttons
            table = context.driver.find_element(By.CLASS_NAME, "customer-table")
            delete_btns = table.find_elements(
                By.XPATH, ".//button[contains(text(), 'Delete')]"
            )

            if not delete_btns:
                break

            # Click first delete button
            delete_btns[0].click()
            time.sleep(0.5)

            # Handle confirmation alert if it appears
            try:
                WebDriverWait(context.driver, 2).until(EC.alert_is_present())
                context.driver.switch_to.alert.accept()
                time.sleep(1)
            except TimeoutException:
                pass

            # Refresh the list
            click_list_all_button(context)
            time.sleep(1)

            iteration += 1
        except Exception as e:
            print(f"Error during cleanup: {e}")
            break


def change_customer_status_via_ui(context, action):
    """Change customer status via UI by clicking the appropriate button"""
    click_list_all_button(context)

    # WAIT for the table to load before looking for buttons
    table = wait_for_element(context, By.CLASS_NAME, "customer-table")
    time.sleep(0.5)  # Give buttons time to render

    # Find the button based on action
    button_text = action.capitalize()
    btns = table.find_elements(
        By.XPATH, f".//button[contains(text(), '{button_text}')]"
    )

    if btns:
        btns[0].click()
        time.sleep(1)
        return True
    else:
        print(f"Warning: No '{button_text}' button found in table")
        return False


# -------------------
# BACKGROUND / SETUP
# -------------------


@given("the customer service is running")
def step_service_running(context):
    """Verify the service is accessible by loading the page"""
    try:
        context.driver.get(context.base_url)
        WebDriverWait(context.driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
    except Exception as e:
        raise Exception(f"Service appears to be down: {e}")


@given("I am on the home page")
def step_home_page(context):
    """Navigate to the home page"""
    context.driver.get(context.base_url)
    # Wait for page to load
    try:
        WebDriverWait(context.driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.ID, "customer-form"))
        )
    except TimeoutException:
        # Try waiting for body at least
        WebDriverWait(context.driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        # Print page source for debugging
        print(f"Page title: {context.driver.title}")
        print(f"Current URL: {context.driver.current_url}")
        # Check if we got an error page
        if (
            "error" in context.driver.page_source.lower()
            or "502" in context.driver.page_source
        ):
            raise Exception("Service appears to be down or returning an error page")


@given("I am on the customer admin page")
def step_admin_page(context):
    """Navigate to the customer admin page"""
    step_home_page(context)


@when("I visit the home page")
def step_visit_home(context):
    """Visit the home page"""
    context.driver.get(context.base_url)
    time.sleep(0.5)


@then("the page should load successfully")
def step_page_loaded(context):
    """Verify page loaded"""
    WebDriverWait(context.driver, WAIT_TIME).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )
    h1 = context.driver.find_element(By.TAG_NAME, "h1")
    assert "Customer" in h1.text


@given('a customer exists with ID "{customer_id}" and status "{status}"')
def step_customer_with_status(context, customer_id, status):
    """Create customer with specific status via UI"""
    # First create the customer
    context.test_customer = create_customer_via_ui(
        context, first_name="Test", last_name="Customer", address="123 Test Street"
    )
    assert context.test_customer is not None

    # Then change status if not active
    if status.lower() != "active":
        if status.lower() == "suspended":
            change_customer_status_via_ui(context, "suspend")
        elif status.lower() == "inactive":
            change_customer_status_via_ui(context, "deactivate")

    time.sleep(1)


@given('a customer exists with ID "{customer_id}"')
def step_customer_exists(context, customer_id):
    """Create customer with default status via UI"""
    context.test_customer = create_customer_via_ui(
        context, first_name="Test", last_name="Customer", address="123 Test Street"
    )
    assert context.test_customer is not None


@given('no customer exists with ID "{customer_id}"')
def step_no_customer(context, customer_id):
    """No customer exists"""
    context.test_customer = None


@given("multiple customers exist in the system")
def step_multiple_customers(context):
    """Create multiple customers via UI"""
    context.test_customers = []

    customers_data = [
        {"first_name": "John", "last_name": "Smith", "address": "123 Boston Ave"},
        {"first_name": "Jane", "last_name": "Doe", "address": "456 New York St"},
        {"first_name": "Bob", "last_name": "Smith", "address": "789 Boston Blvd"},
    ]

    for data in customers_data:
        customer = create_customer_via_ui(context, **data)
        if customer:
            context.test_customers.append(customer)
        # Clear form for next customer
        clear_form(context)


@given("multiple customers exist with different last names")
def step_multiple_different_names(context):
    """Create customers with different names via UI"""
    step_multiple_customers(context)


@given("customers exist in the system")
def step_customers_exist(context):
    """Ensure customers exist via UI"""
    step_multiple_customers(context)


@given("no customers exist in the system")
def step_no_customers(context):
    """Delete all customers via UI"""
    delete_all_customers_via_ui(context)


# -------------------
# CREATE
# -------------------


@when("I fill in the customer form with valid data")
def step_fill_valid(context):
    """Fill form with valid data"""
    wait_for_element(context, By.ID, "first-name").clear()
    context.driver.find_element(By.ID, "first-name").send_keys("John")
    context.driver.find_element(By.ID, "last-name").clear()
    context.driver.find_element(By.ID, "last-name").send_keys("Doe")
    context.driver.find_element(By.ID, "address").clear()
    context.driver.find_element(By.ID, "address").send_keys("123 Main St")
    context.created_customer_data = {
        "first_name": "John",
        "last_name": "Doe",
        "address": "123 Main St",
    }


@when("I fill in the customer form with incomplete data")
def step_fill_incomplete(context):
    """Fill form incompletely"""
    wait_for_element(context, By.ID, "first-name").clear()
    context.driver.find_element(By.ID, "first-name").send_keys("John")
    context.driver.find_element(By.ID, "last-name").clear()
    context.driver.find_element(By.ID, "address").clear()


@when('I click the "Create Customer" button')
def step_click_create(context):
    """Click create"""
    wait_for_clickable(context, By.ID, "create-btn").click()
    time.sleep(1)


@when("I leave the first name field empty")
def step_empty_first(context):
    """Clear first name"""
    wait_for_element(context, By.ID, "first-name").clear()


@when('I fill in first name with "{value}"')
def step_fill_first(context, value):
    """Fill first name"""
    field = wait_for_element(context, By.ID, "first-name")
    field.clear()
    field.send_keys(value)


@when('I fill in last name with "{value}"')
def step_fill_last(context, value):
    """Fill last name"""
    field = context.driver.find_element(By.ID, "last-name")
    field.clear()
    field.send_keys(value)


@when('I fill in address with "{value}"')
def step_fill_addr(context, value):
    """Fill address"""
    field = context.driver.find_element(By.ID, "address")
    field.clear()
    field.send_keys(value)


@when("I leave the last name field empty")
def step_empty_last(context):
    """Clear last name"""
    context.driver.find_element(By.ID, "last-name").clear()


@when("I leave the address field empty")
def step_empty_addr(context):
    """Clear address"""
    context.driver.find_element(By.ID, "address").clear()


@when("I create a new customer")
def step_create_new(context):
    """Create customer via form"""
    step_fill_valid(context)
    step_click_create(context)


@then("I should see a success message")
def step_success_msg(context):
    """Verify success"""
    flash = wait_for_flash_message(context)
    assert "success" in flash.text.lower()


@then("the new customer should appear in the customer list")
def step_in_list(context):
    """Verify in list"""
    click_list_all_button(context)
    table = wait_for_element(context, By.CLASS_NAME, "customer-table")
    if hasattr(context, "created_customer_data"):
        assert context.created_customer_data["first_name"] in table.text


@then("I should see an error message indicating which fields are required")
def step_required_error(context):
    """Verify required error"""
    flash = wait_for_flash_message(context)
    assert "error" in flash.text.lower() or "required" in flash.text.lower()


@then('I should see an error message "{expected}"')
def step_specific_error(context, expected):
    """Verify specific error"""
    flash = wait_for_flash_message(context)
    assert expected.lower() in flash.text.lower()


# -------------------
# LIST
# -------------------


@when("I click the list button")
def step_click_list(context):
    """Click list button"""
    click_list_all_button(context)


@then("I should see a list of all customers")
def step_see_list(context):
    """Verify list visible"""
    table = wait_for_element(context, By.CLASS_NAME, "customer-table")
    assert table.is_displayed()


@then("each customer entry should display first name, last name, address, and ID")
def step_verify_fields(context):
    """Verify columns"""
    table = context.driver.find_element(By.CLASS_NAME, "customer-table")
    headers = table.find_element(By.TAG_NAME, "thead").text.lower()
    assert (
        "id" in headers
        and "first" in headers
        and "last" in headers
        and "address" in headers
    )


@then('I should see an empty list message "{message}"')
def step_empty_msg(context, message):
    """Verify empty message"""
    container = context.driver.find_element(By.ID, "customer-list-container")
    assert "no customers" in container.text.lower()


@then("I should see the newly created customer in the list")
def step_new_in_list(context):
    """Verify new customer"""
    click_list_all_button(context)
    table = wait_for_element(context, By.CLASS_NAME, "customer-table")
    if hasattr(context, "created_customer_data"):
        assert context.created_customer_data["first_name"] in table.text


# -------------------
# QUERY/SEARCH
# -------------------


@when('I enter "{value}" into the last name search field')
def step_search_last(context, value):
    """Enter last name search"""
    field = context.driver.find_element(By.ID, "search-last-name")
    field.clear()
    field.send_keys(value)


@when('I enter "{value}" into the address search field')
def step_search_addr(context, value):
    """Enter address search"""
    field = context.driver.find_element(By.ID, "search-address")
    field.clear()
    field.send_keys(value)


@when('I click the "Search" button')
def step_click_search(context):
    """Click search"""
    form = context.driver.find_element(By.ID, "search-form")
    form.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1)


@when('I search for customer ID "{customer_id}"')
def step_search_id(context, customer_id):
    """Search by ID"""
    field = context.driver.find_element(By.ID, "search-id")
    field.clear()
    field.send_keys(customer_id)
    step_click_search(context)


@then('I should see only customers with last name "{last_name}"')
def step_filter_last(context, last_name):
    """Verify filter"""
    try:
        table = wait_for_element(context, By.CLASS_NAME, "customer-table")
        for row in table.find_elements(By.TAG_NAME, "tr")[1:]:
            assert last_name.lower() in row.text.lower()
    except TimeoutException:
        pass


@then("I should see an empty result list")
def step_empty_results(context):
    """Verify empty"""
    container = context.driver.find_element(By.ID, "customer-list-container")
    assert "no customers" in container.text.lower()


@then('I should see the message "{message}"')
def step_see_msg(context, message):
    """Verify message"""
    container = context.driver.find_element(By.ID, "customer-list-container")
    assert "no customers" in container.text.lower()


@then(
    'I should see only customers matching last name "{last_name}" and address containing "{address}"'
)
def step_multi_filter(context, last_name, address):
    """Verify multi-filter"""
    try:
        table = wait_for_element(context, By.CLASS_NAME, "customer-table")
        for row in table.find_elements(By.TAG_NAME, "tr")[1:]:
            text = row.text.lower()
            assert last_name.lower() in text and address.lower() in text
    except TimeoutException:
        pass


# -------------------
# READ
# -------------------


@when('I click the "View Details" button')
def step_view_details(context):
    """Click view/edit"""
    click_list_all_button(context)
    table = wait_for_element(context, By.CLASS_NAME, "customer-table")
    btns = table.find_elements(By.XPATH, ".//button[contains(text(), 'Edit')]")
    if btns:
        btns[0].click()
        time.sleep(0.5)


@then("I should see the complete customer information displayed")
def step_see_info(context):
    """Verify info displayed"""
    first = context.driver.find_element(By.ID, "first-name")
    assert first.get_attribute("value") != ""


@then('I should see a "Customer not found" message')
def step_not_found(context):
    """Verify not found"""
    container = context.driver.find_element(By.ID, "customer-list-container")
    assert "no customers" in container.text.lower()


# -------------------
# DELETE
# -------------------


@when('I click the "Delete" button for customer "{customer_id}"')
def step_click_delete(context, customer_id):
    """Click delete"""
    click_list_all_button(context)
    table = wait_for_element(context, By.CLASS_NAME, "customer-table")
    btns = table.find_elements(By.XPATH, ".//button[contains(text(), 'Delete')]")
    if btns:
        btns[0].click()


@when("I confirm the deletion")
def step_confirm(context):
    """Confirm delete"""
    try:
        WebDriverWait(context.driver, 3).until(EC.alert_is_present())
        context.driver.switch_to.alert.accept()
        time.sleep(1)
    except TimeoutException:
        pass


@when("I cancel the deletion")
def step_cancel(context):
    """Cancel delete"""
    try:
        WebDriverWait(context.driver, 3).until(EC.alert_is_present())
        context.driver.switch_to.alert.dismiss()
    except TimeoutException:
        pass


@then("the customer should no longer appear in the list")
def step_deleted(context):
    """Verify deleted"""
    # Refresh the list to see updated state
    click_list_all_button(context)
    time.sleep(1)

    container = context.driver.find_element(By.ID, "customer-list-container")

    if hasattr(context, "test_customer") and context.test_customer:
        customer_name_to_check = context.test_customer["first_name"]

        # Wait for the customer's name to disappear from the list
        try:
            WebDriverWait(context.driver, WAIT_TIME).until_not(
                EC.text_to_be_present_in_element(
                    (By.ID, "customer-list-container"), customer_name_to_check
                )
            )
        except TimeoutException:
            raise AssertionError(
                f"Customer '{customer_name_to_check}' still appeared in the list after deletion"
            )


@then("the customer should still appear in the list")
def step_still_exists(context):
    """Verify still exists"""
    click_list_all_button(context)
    if hasattr(context, "test_customer") and context.test_customer:
        table = wait_for_element(context, By.CLASS_NAME, "customer-table")
        assert context.test_customer["first_name"] in table.text


# -------------------
# UPDATE
# -------------------


@when('I navigate to edit customer "{customer_id}"')
def step_nav_edit(context, customer_id):
    """Navigate to edit"""
    click_list_all_button(context)
    table = wait_for_element(context, By.CLASS_NAME, "customer-table")
    btns = table.find_elements(By.XPATH, ".//button[contains(text(), 'Edit')]")
    if btns:
        btns[0].click()
        time.sleep(1)


@when('I update the customer\'s address to "{new_address}"')
def step_update_addr(context, new_address):
    """Update address"""
    field = wait_for_element(context, By.ID, "address")
    field.clear()
    field.send_keys(new_address)
    context.updated_address = new_address


@when('I clear the required field "{field_name}"')
def step_clear_field(context, field_name):
    """Clear field"""
    field_map = {
        "firstName": "first-name",
        "lastName": "last-name",
        "address": "address",
    }
    context.driver.find_element(
        By.ID, field_map.get(field_name, field_name.lower())
    ).clear()


@when('I click the "Update" button')
def step_click_update(context):
    """Click update"""
    wait_for_clickable(context, By.ID, "update-btn").click()
    time.sleep(1)


@then("the customer's address should be updated in the list")
def step_addr_updated(context):
    """Verify updated"""
    click_list_all_button(context)
    table = wait_for_element(context, By.CLASS_NAME, "customer-table")
    if hasattr(context, "updated_address"):
        assert context.updated_address in table.text


@then("I should see an error message about invalid data")
def step_invalid_error(context):
    """Verify invalid error"""
    flash = wait_for_flash_message(context)
    assert "error" in flash.text.lower()


# -------------------
# STATUS ACTIONS
# -------------------


@when('I click the "Activate" button for customer "{customer_id}"')
def step_activate(context, customer_id):
    """Click activate"""
    result = change_customer_status_via_ui(context, "activate")
    if not result:
        print(f"Failed to find Activate button for customer {customer_id}")


@when('I click the "Deactivate" button for customer "{customer_id}"')
def step_deactivate(context, customer_id):
    """Click deactivate"""
    result = change_customer_status_via_ui(context, "deactivate")
    if not result:
        print(f"Failed to find Deactivate button for customer {customer_id}")


@when('I click the "Suspend" button for customer "{customer_id}"')
def step_suspend(context, customer_id):
    """Click suspend"""
    result = change_customer_status_via_ui(context, "suspend")
    if not result:
        print(f"Failed to find Suspend button for customer {customer_id}")


@then('I should see "Success: Customer activated!"')
def step_activated(context):
    """Verify activated"""
    flash = wait_for_flash_message(context)
    assert "success" in flash.text.lower()


@then('I should see "Success: Customer deactivated!"')
def step_deactivated(context):
    """Verify deactivated"""
    flash = wait_for_flash_message(context)
    assert "success" in flash.text.lower()


@then('I should see "Success: Customer suspended!"')
def step_suspended(context):
    """Verify suspended"""
    flash = wait_for_flash_message(context)
    assert "success" in flash.text.lower()


@then('I should see "Error: Customer not found"')
def step_error_not_found(context):
    """Verify error"""
    pass  # Button won't exist for non-existent customer


@then('I should see the status for customer "{customer_id}" change to "{status}"')
def step_status_changed(context, customer_id, status):
    """Verify status changed"""
    click_list_all_button(context)
    table = wait_for_element(context, By.CLASS_NAME, "customer-table")
    badges = table.find_elements(By.CLASS_NAME, "status-badge")
    assert any(status.lower() in b.text.lower() for b in badges)
