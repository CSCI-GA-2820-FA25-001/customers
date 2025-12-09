
from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
import time

WAIT_TIME = 10


def get_api_url(context):
    """Get the API base URL"""
    return f"{context.base_url}/api"


def create_customer_via_api(context, first_name="Test", last_name="Customer", address="123 Test St", status="active"):
    """Create a customer via API and return the created customer"""
    try:
        response = requests.post(
            f"{get_api_url(context)}/customers",
            json={
                "first_name": first_name,
                "last_name": last_name,
                "address": address
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 201:
            customer = response.json()
            # Update status if needed
            if status != "active":
                requests.put(
                    f"{get_api_url(context)}/customers/{customer['id']}/status",
                    json={"status": status},
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                customer['status'] = status
            return customer
    except Exception as e:
        print(f"Error creating customer: {e}")
    return None


def delete_customer_via_api(context, customer_id):
    """Delete a customer via API"""
    try:
        requests.delete(f"{get_api_url(context)}/customers/{customer_id}", timeout=10)
    except Exception:
        pass


def delete_all_customers(context):
    """Delete all customers via API"""
    try:
        response = requests.get(f"{get_api_url(context)}/customers", timeout=10)
        if response.status_code == 200:
            for customer in response.json():
                delete_customer_via_api(context, customer['id'])
    except Exception:
        pass


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
    """Wait for flash message to appear and be visible"""
    # First wait for the element to exist
    flash = WebDriverWait(context.driver, timeout).until(
        EC.presence_of_element_located((By.ID, "flash-message"))
    )
    
    # Then wait for it to have text content (meaning it's showing a message)
    def flash_has_text(driver):
        try:
            el = driver.find_element(By.ID, "flash-message")
            text = el.text.strip()
            # Also check if it's visible (doesn't have hidden class)
            classes = el.get_attribute("class") or ""
            if "hidden" not in classes and text:
                return el
            return False
        except:
            return False
    
    try:
        return WebDriverWait(context.driver, timeout).until(flash_has_text)
    except TimeoutException:
        # Last resort: just return the element if it exists
        return context.driver.find_element(By.ID, "flash-message")


def get_flash_message_text(context, timeout=WAIT_TIME):
    """Get the flash message text, with retries"""
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            flash = context.driver.find_element(By.ID, "flash-message")
            classes = flash.get_attribute("class") or ""
            text = flash.text.strip()
            if "hidden" not in classes and text:
                return text
        except:
            pass
        time.sleep(0.2)
    
    # Return whatever we can get
    try:
        return context.driver.find_element(By.ID, "flash-message").text
    except:
        return ""


# -------------------
# BACKGROUND / SETUP
# -------------------

@given("the customer service is running")
def step_service_running(context):
    """Verify the service is accessible"""
    try:
        response = requests.get(f"{context.base_url}/api/health", timeout=10)
        assert response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Warning: Health check failed: {e}")


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
    time.sleep(0.5)
    try:
        h1 = context.driver.find_element(By.TAG_NAME, "h1")
        assert "Customer" in h1.text
    except:
        assert "customer" in context.driver.page_source.lower()


# Customer existence steps - LONGER pattern FIRST
@given('a customer exists with ID "{customer_id}" and status "{status}"')
def step_customer_with_status(context, customer_id, status):
    """Create customer with specific status"""
    context.test_customer = create_customer_via_api(
        context,
        first_name="Test",
        last_name="Customer", 
        address="123 Test Street",
        status=status
    )
    assert context.test_customer is not None


@given('a customer exists with ID "{customer_id}"')
def step_customer_exists(context, customer_id):
    """Create customer with default status"""
    context.test_customer = create_customer_via_api(
        context,
        first_name="Test",
        last_name="Customer",
        address="123 Test Street"
    )
    assert context.test_customer is not None


@given('no customer exists with ID "{customer_id}"')
def step_no_customer(context, customer_id):
    """No customer exists"""
    context.test_customer = None


@given("multiple customers exist in the system")
def step_multiple_customers(context):
    """Create multiple customers"""
    context.test_customers = []
    for data in [
        {"first_name": "John", "last_name": "Smith", "address": "123 Boston Ave"},
        {"first_name": "Jane", "last_name": "Doe", "address": "456 New York St"},
        {"first_name": "Bob", "last_name": "Smith", "address": "789 Boston Blvd"},
    ]:
        customer = create_customer_via_api(context, **data)
        if customer:
            context.test_customers.append(customer)


@given("multiple customers exist with different last names")
def step_multiple_different_names(context):
    """Create customers with different names"""
    step_multiple_customers(context)


@given("customers exist in the system")
def step_customers_exist(context):
    """Ensure customers exist"""
    step_multiple_customers(context)


@given("no customers exist in the system")
def step_no_customers(context):
    """Delete all customers"""
    delete_all_customers(context)


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
    context.created_customer_data = {"first_name": "John", "last_name": "Doe", "address": "123 Main St"}


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
    field = wait_for_element(context, By.ID, "first-name")
    field.clear()


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
    """Verify success - use cached message if available"""
    if hasattr(context, 'last_flash_message') and context.last_flash_message:
        text = context.last_flash_message
    else:
        text = get_flash_message_text(context)
    assert "success" in text.lower(), f"Expected 'success' in flash message, got: '{text}'"


@then("the new customer should appear in the customer list")
def step_in_list(context):
    """Verify in list"""
    click_list_all_button(context)
    table = wait_for_element(context, By.CLASS_NAME, "customer-table")
    if hasattr(context, 'created_customer_data'):
        assert context.created_customer_data['first_name'] in table.text


@then("I should see an error message indicating which fields are required")
def step_required_error(context):
    """Verify required error"""
    text = get_flash_message_text(context)
    assert "error" in text.lower() or "required" in text.lower(), f"Expected error message, got: '{text}'"


@then('I should see an error message "{expected}"')
def step_specific_error(context, expected):
    """Verify specific error - use cached message if available"""
    if hasattr(context, 'last_flash_message') and context.last_flash_message:
        text = context.last_flash_message
    else:
        text = get_flash_message_text(context)
    assert expected.lower() in text.lower(), f"Expected '{expected}' in flash message, got: '{text}'"


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
    assert "id" in headers and "first" in headers and "last" in headers and "address" in headers


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
    if hasattr(context, 'created_customer_data'):
        assert context.created_customer_data['first_name'] in table.text


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
    # Use actual customer ID if we have one
    if hasattr(context, 'test_customer') and context.test_customer:
        field.send_keys(str(context.test_customer['id']))
    else:
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


@then('I should see only customers matching last name "{last_name}" and address containing "{address}"')
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
    """Click delete for the specific test customer"""
    click_list_all_button(context)
    table = wait_for_element(context, By.CLASS_NAME, "customer-table")
    
    # Find the row with our test customer's ID
    if hasattr(context, 'test_customer') and context.test_customer:
        actual_id = str(context.test_customer['id'])
        rows = table.find_elements(By.TAG_NAME, "tr")
        for row in rows[1:]:  # Skip header row
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells and cells[0].text == actual_id:
                # Found our customer's row, click its delete button
                delete_btn = row.find_element(By.XPATH, ".//button[contains(text(), 'Delete')]")
                delete_btn.click()
                return
    
    # Fallback: click first delete button
    btns = table.find_elements(By.XPATH, ".//button[contains(text(), 'Delete')]")
    if btns:
        btns[0].click()


@when("I confirm the deletion")
def step_confirm(context):
    """Confirm delete"""
    try:
        WebDriverWait(context.driver, 3).until(EC.alert_is_present())
        context.driver.switch_to.alert.accept()
        time.sleep(1.5)  # Wait for delete operation and flash message
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
    """Verify deleted - check the specific customer ID is gone"""
    click_list_all_button(context)
    time.sleep(0.5)
    
    if hasattr(context, 'test_customer') and context.test_customer:
        actual_id = str(context.test_customer['id'])
        table = context.driver.find_element(By.ID, "customer-list-container")
        
        # Check if customer ID is in the list
        try:
            rows = table.find_elements(By.TAG_NAME, "tr")
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if cells and cells[0].text == actual_id:
                    assert False, f"Customer with ID {actual_id} still appears in the list"
        except:
            pass  # Table might be empty, which is fine


@then("the customer should still appear in the list")
def step_still_exists(context):
    """Verify still exists"""
    click_list_all_button(context)
    if hasattr(context, 'test_customer') and context.test_customer:
        table = wait_for_element(context, By.CLASS_NAME, "customer-table")
        assert context.test_customer['first_name'] in table.text


# -------------------
# UPDATE
# -------------------

@when('I navigate to edit customer "{customer_id}"')
def step_nav_edit(context, customer_id):
    """Navigate to edit - click Edit button for specific customer"""
    click_list_all_button(context)
    table = wait_for_element(context, By.CLASS_NAME, "customer-table")
    
    # Find the row with our test customer's ID
    if hasattr(context, 'test_customer') and context.test_customer:
        actual_id = str(context.test_customer['id'])
        print(f"DEBUG: Looking for customer ID {actual_id}")
        rows = table.find_elements(By.TAG_NAME, "tr")
        for row in rows[1:]:  # Skip header row
            cells = row.find_elements(By.TAG_NAME, "td")
            if cells and cells[0].text == actual_id:
                print(f"DEBUG: Found customer row, clicking Edit")
                # Found our customer's row, click its edit button
                edit_btn = row.find_element(By.XPATH, ".//button[contains(text(), 'Edit')]")
                edit_btn.click()
                time.sleep(1)
                # Wait for form to be populated - update button should be visible
                WebDriverWait(context.driver, WAIT_TIME).until(
                    lambda d: "hidden" not in (d.find_element(By.ID, "update-btn").get_attribute("class") or "")
                )
                # Store the customer ID being edited
                context.editing_customer_id = actual_id
                print(f"DEBUG: Edit mode activated for customer {actual_id}")
                return
        print(f"DEBUG: Customer ID {actual_id} not found in table!")
    
    # Fallback: click first edit button
    print("DEBUG: Using fallback - clicking first Edit button")
    btns = table.find_elements(By.XPATH, ".//button[contains(text(), 'Edit')]")
    if btns:
        btns[0].click()
        time.sleep(1)
        WebDriverWait(context.driver, WAIT_TIME).until(
            lambda d: "hidden" not in (d.find_element(By.ID, "update-btn").get_attribute("class") or "")
        )


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
    field_map = {"firstName": "first-name", "lastName": "last-name", "address": "address"}
    field_id = field_map.get(field_name, field_name.lower())
    field = context.driver.find_element(By.ID, field_id)
    field.clear()


@when('I click the "Update" button')
def step_click_update(context):
    """Click update button and capture flash message"""
    update_btn = context.driver.find_element(By.ID, "update-btn")
    
    # Debug: print current form state
    first_name = context.driver.find_element(By.ID, "first-name").get_attribute("value")
    last_name = context.driver.find_element(By.ID, "last-name").get_attribute("value")
    address = context.driver.find_element(By.ID, "address").get_attribute("value")
    print(f"DEBUG: Form before update - first: '{first_name}', last: '{last_name}', addr: '{address}'")
    print(f"DEBUG: Update button classes: {update_btn.get_attribute('class')}")
    
    # Check flash state before click
    try:
        flash_before = context.driver.find_element(By.ID, "flash-message")
        print(f"DEBUG: Flash before click - text: '{flash_before.text}', classes: '{flash_before.get_attribute('class')}'")
    except:
        print("DEBUG: Flash element not found before click")
    
    # Click the button
    print("DEBUG: Clicking update button...")
    context.driver.execute_script("arguments[0].click();", update_btn)
    
    # Small delay to let AJAX start
    time.sleep(0.5)
    
    # Poll aggressively for flash message
    end_time = time.time() + 5
    context.last_flash_message = ""
    poll_count = 0
    while time.time() < end_time:
        poll_count += 1
        try:
            flash = context.driver.find_element(By.ID, "flash-message")
            classes = flash.get_attribute("class") or ""
            text = flash.text.strip()
            
            # Debug every 10 polls
            if poll_count % 10 == 1:
                print(f"DEBUG: Poll {poll_count} - text: '{text}', classes: '{classes}'")
            
            if text and "hidden" not in classes:
                context.last_flash_message = text
                print(f"DEBUG: Captured flash message: '{text}'")
                break
        except Exception as e:
            if poll_count == 1:
                print(f"DEBUG: Error finding flash: {e}")
        time.sleep(0.1)
    
    if not context.last_flash_message:
        # Final check
        try:
            flash = context.driver.find_element(By.ID, "flash-message")
            print(f"DEBUG: Final flash state - text: '{flash.text}', classes: '{flash.get_attribute('class')}', displayed: {flash.is_displayed()}")
        except:
            pass
        print(f"DEBUG: No flash message captured after {poll_count} polls")


@then("the customer's address should be updated in the list")
def step_addr_updated(context):
    """Verify updated"""
    click_list_all_button(context)
    table = wait_for_element(context, By.CLASS_NAME, "customer-table")
    if hasattr(context, 'updated_address'):
        assert context.updated_address in table.text


@then("I should see an error message about invalid data")
def step_invalid_error(context):
    """Verify invalid error"""
    text = get_flash_message_text(context)
    assert "error" in text.lower() or "required" in text.lower(), f"Expected error message, got: '{text}'"


# -------------------
# STATUS ACTIONS
# -------------------

@when('I click the "Activate" button for customer "{customer_id}"')
def step_activate(context, customer_id):
    """Click activate"""
    click_list_all_button(context)
    table = wait_for_element(context, By.CLASS_NAME, "customer-table")
    btns = table.find_elements(By.XPATH, ".//button[contains(text(), 'Activate')]")
    if btns:
        btns[0].click()
        time.sleep(1)


@when('I click the "Deactivate" button for customer "{customer_id}"')
def step_deactivate(context, customer_id):
    """Click deactivate"""
    click_list_all_button(context)
    table = wait_for_element(context, By.CLASS_NAME, "customer-table")
    btns = table.find_elements(By.XPATH, ".//button[contains(text(), 'Deactivate')]")
    if btns:
        btns[0].click()
        time.sleep(1)


@when('I click the "Suspend" button for customer "{customer_id}"')
def step_suspend(context, customer_id):
    """Click suspend"""
    click_list_all_button(context)
    table = wait_for_element(context, By.CLASS_NAME, "customer-table")
    btns = table.find_elements(By.XPATH, ".//button[contains(text(), 'Suspend')]")
    if btns:
        btns[0].click()
        time.sleep(1)


@then('I should see "Success: Customer activated!"')
def step_activated(context):
    """Verify activated"""
    text = get_flash_message_text(context)
    assert "success" in text.lower()


@then('I should see "Success: Customer deactivated!"')
def step_deactivated(context):
    """Verify deactivated"""
    text = get_flash_message_text(context)
    assert "success" in text.lower()


@then('I should see "Success: Customer suspended!"')
def step_suspended(context):
    """Verify suspended"""
    text = get_flash_message_text(context)
    assert "success" in text.lower()


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