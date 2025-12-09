from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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
    context.driver.get(context.base_url)
    try:
        wait_for_element(context, By.ID, "customer-form", timeout=30)
    except TimeoutException:
        # Try to check if page loaded at all
        assert "Customer" in context.driver.page_source, "Service not accessible"


@given("I am on the home page")
def step_home_page(context):
    """Navigate to the home page"""
    context.driver.get(context.base_url)
    wait_for_element(context, By.ID, "customer-form")


@given("the following customers exist:")
def step_customers_exist_table(context):
    """Create customers from a data table using the UI"""
    for row in context.table:
        first_name = row["first_name"]
        last_name = row["last_name"]
        address = row["address"]
        status = row.get("status", "active")
        
        create_customer_via_ui(context, first_name, last_name, address, status)
    
    # Clear the form after creating customers
    clear_btn = context.driver.find_element(By.ID, "clear-btn")
    clear_btn.click()


@given("there are no customers")
def step_no_customers(context):
    """Delete all customers using the UI"""
    delete_all_customers_via_ui(context)


# ============================================================================
# WHEN STEPS - User Actions
# ============================================================================

@when("I visit the home page")
def step_visit_home(context):
    """Visit the home page"""
    context.driver.get(context.base_url)
    time.sleep(0.5)


@when('I set the "{field_name}" to "{value}"')
def step_set_field(context, field_name, value):
    """Set a form field to a value"""
    field_id = get_field_id(field_name)
    field = wait_for_element(context, By.ID, field_id)
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


# ============================================================================
# THEN STEPS - Assertions
# ============================================================================

@then("the page should load successfully")
def step_page_loaded(context):
    """Verify the page loaded"""
    h1 = wait_for_element(context, By.TAG_NAME, "h1")
    assert "Customer" in h1.text, f"Expected 'Customer' in page title, got: {h1.text}"


@then('I should see the message "{expected_message}"')
def step_see_message(context, expected_message):
    """Verify a message is displayed"""
    # Check cached flash message first
    if hasattr(context, 'last_flash_message') and context.last_flash_message:
        text = context.last_flash_message
    else:
        text = get_flash_message_text(context)
    
    # Also check the customer list container for "No customers" type messages
    if not text or expected_message.lower() not in text.lower():
        try:
            container = context.driver.find_element(By.ID, "customer-list-container")
            container_text = container.text
            if expected_message.lower() in container_text.lower():
                return  # Found in container
        except:
            pass
    
    assert expected_message.lower() in text.lower(), \
        f"Expected message containing '{expected_message}', got: '{text}'"


@then('I should see "{text}" in the results')
def step_see_in_results(context, text):
    """Verify text appears in the customer list"""
    container = wait_for_element(context, By.ID, "customer-list-container")
    assert text.lower() in container.text.lower(), \
        f"Expected '{text}' in results, got: {container.text}"


@then('I should not see "{text}" in the results')
def step_not_see_in_results(context, text):
    """Verify text does NOT appear in the customer list"""
    container = context.driver.find_element(By.ID, "customer-list-container")
    assert text.lower() not in container.text.lower(), \
        f"Did not expect '{text}' in results, but found it in: {container.text}"


@then('I should see the status change to "{status}" for customer "{customer_name}"')
def step_see_status_change(context, status, customer_name):
    """Verify a customer's status has changed"""
    # Refresh the list
    list_btn = wait_for_clickable(context, By.ID, "list-all-btn")
    list_btn.click()
    time.sleep(1)
    
    row = find_customer_row(context, customer_name)
    assert row is not None, f"Customer '{customer_name}' not found"
    
    # Find the status badge in the row
    badge = row.find_element(By.CLASS_NAME, "status-badge")
    assert status.lower() in badge.text.lower(), \
        f"Expected status '{status}', got: {badge.text}"


@then('the "{field_name}" field should contain "{expected_value}"')
def step_field_contains(context, field_name, expected_value):
    """Verify a form field contains an expected value"""
    field_id = get_field_id(field_name)
    field = context.driver.find_element(By.ID, field_id)
    actual_value = field.get_attribute("value")
    assert expected_value.lower() in actual_value.lower(), \
        f"Expected field '{field_name}' to contain '{expected_value}', got: '{actual_value}'"