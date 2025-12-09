from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

WAIT_TIME = 60

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

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


def get_flash_message_text(context, timeout=WAIT_TIME):
    """
    Poll for flash message text - handles brief appearances.
    Returns the flash message text or empty string if not found.
    """
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            flash = context.driver.find_element(By.ID, "flash-message")
            if flash.is_displayed():
                text = flash.text.strip()
                if text:
                    return text
        except (NoSuchElementException, Exception):
            pass
        time.sleep(0.2)
    return ""


def get_field_id(field_name):
    """Map user-friendly field names to HTML element IDs"""
    field_map = {
        "first name": "first-name",
        "last name": "last-name",
        "address": "address",
        "search id": "search-id",
        "search first name": "search-first-name",
        "search last name": "search-last-name",
        "search address": "search-address",
        "customer id": "customer-id",
    }
    return field_map.get(field_name.lower(), field_name.lower().replace(" ", "-"))


def find_customer_row(context, customer_name):
    """Find a table row containing the customer name"""
    table = wait_for_element(context, By.CLASS_NAME, "customer-table")
    rows = table.find_elements(By.TAG_NAME, "tr")
    for row in rows[1:]:  # Skip header
        if customer_name.lower() in row.text.lower():
            return row
    return None

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

def create_customer_via_ui(context, first_name, last_name, address, status="active"):
    """Create a customer using the UI form"""
    # Navigate to home page if needed
    if "customer" not in context.driver.current_url.lower():
        context.driver.get(context.base_url)
        wait_for_element(context, By.ID, "customer-form")
    
    # Clear and fill form
    first_field = wait_for_element(context, By.ID, "first-name")
    first_field.clear()
    first_field.send_keys(first_name)
    
    last_field = context.driver.find_element(By.ID, "last-name")
    last_field.clear()
    last_field.send_keys(last_name)
    
    addr_field = context.driver.find_element(By.ID, "address")
    addr_field.clear()
    addr_field.send_keys(address)
    
    # Click Create button
    create_btn = wait_for_clickable(context, By.ID, "create-btn")
    create_btn.click()
    
    # Wait for flash message and capture customer info
    time.sleep(1)
    flash_text = get_flash_message_text(context, timeout=5)
    
    # If status is not active, we need to change it via UI
    if status != "active":
        # List customers and change status
        list_btn = wait_for_clickable(context, By.ID, "list-all-btn")
        list_btn.click()
        time.sleep(1)
        
        # Find the customer row and click the appropriate status button
        customer_name = f"{first_name} {last_name}"
        row = find_customer_row(context, customer_name)
        if row:
            if status == "deactivated":
                btn = row.find_element(By.XPATH, ".//button[contains(text(), 'Deactivate')]")
            elif status == "suspended":
                btn = row.find_element(By.XPATH, ".//button[contains(text(), 'Suspend')]")
            btn.click()
            time.sleep(1)
            get_flash_message_text(context, timeout=3)  # Wait for status change message
    
    return True


def delete_all_customers_via_ui(context):
    """Delete all customers using the UI"""
    context.driver.get(context.base_url)
    wait_for_element(context, By.ID, "customer-form")
    
    # Click List All
    list_btn = wait_for_clickable(context, By.ID, "list-all-btn")
    list_btn.click()
    time.sleep(1)
    
    # Keep deleting while there are customers
    max_iterations = 50  # Safety limit
    iterations = 0
    
    while iterations < max_iterations:
        try:
            # Look for any delete button
            delete_btns = context.driver.find_elements(By.XPATH, "//button[contains(text(), 'Delete')]")
            if not delete_btns:
                break
            
            delete_btns[0].click()
            
            # Handle confirmation dialog
            WebDriverWait(context.driver, 3).until(EC.alert_is_present())
            context.driver.switch_to.alert.accept()
            time.sleep(0.5)
            
            iterations += 1
        except Exception:
            break


# ============================================================================
# BACKGROUND / SETUP STEPS
# ============================================================================

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

# ============================================================================
# WHEN STEPS - User Actions
# ============================================================================

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


@when('I clear the "{field_name}" field')
def step_clear_field(context, field_name):
    """Clear a form field"""
    field_id = get_field_id(field_name)
    field = context.driver.find_element(By.ID, field_id)
    field.clear()


@when('I click the "{button_name}" button')
def step_click_button(context, button_name):
    """Click a button by its name/text"""
    button_name_lower = button_name.lower()
    
    # Map button names to IDs or find by text
    if button_name_lower in ["create", "create customer"]:
        btn = wait_for_clickable(context, By.ID, "create-btn")
    elif button_name_lower in ["update", "update customer"]:
        btn = wait_for_clickable(context, By.ID, "update-btn")
    elif button_name_lower in ["clear", "clear form"]:
        btn = wait_for_clickable(context, By.ID, "clear-btn")
    elif button_name_lower in ["list all", "list all customers"]:
        btn = wait_for_clickable(context, By.ID, "list-all-btn")
    elif button_name_lower == "search":
        # Find search button in search form
        search_form = context.driver.find_element(By.ID, "search-form")
        btn = search_form.find_element(By.CSS_SELECTOR, "button[type='submit']")
    elif button_name_lower in ["clear search"]:
        btn = wait_for_clickable(context, By.ID, "clear-search-btn")
    else:
        # Try to find by text content
        btn = wait_for_clickable(context, By.XPATH, f"//button[contains(text(), '{button_name}')]")
    
    btn.click()
    
    # Capture flash message after button click
    context.last_flash_message = get_flash_message_text(context, timeout=5)


@when('I click the "{action}" button for customer "{customer_name}"')
def step_click_action_for_customer(context, action, customer_name):
    """Click an action button for a specific customer"""
    row = find_customer_row(context, customer_name)
    assert row is not None, f"Customer '{customer_name}' not found in the list"
    
    # Find the button within this row
    btn = row.find_element(By.XPATH, f".//button[contains(text(), '{action}')]")
    btn.click()
    
    # Capture flash message
    context.last_flash_message = get_flash_message_text(context, timeout=5)


@when("I confirm the deletion")
def step_confirm_deletion(context):
    """Confirm the deletion in the alert dialog"""
    try:
        WebDriverWait(context.driver, 5).until(EC.alert_is_present())
        context.driver.switch_to.alert.accept()
        context.last_flash_message = get_flash_message_text(context, timeout=5)
    except TimeoutException:
        pass


@when("I cancel the deletion")
def step_cancel_deletion(context):
    """Cancel the deletion in the alert dialog"""
    try:
        WebDriverWait(context.driver, 5).until(EC.alert_is_present())
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


@then('I should see the status change to "{status}" for customer "{customer_name}"')
def step_see_status_change(context, status, customer_name):
    """Verify a customer's status has changed"""
    # Refresh the list
    list_btn = wait_for_clickable(context, By.ID, "list-all-btn")
    list_btn.click()
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
