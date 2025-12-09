######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""
Customer Steps

Steps file for Customer.feature

For information on Waiting until elements are present in the HTML see:
    https://selenium-python.readthedocs.io/waits.html
"""
import requests
from compare3 import expect
from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

# HTTP Return Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204

WAIT_TIMEOUT = 60


@given('the following customers')
def step_impl(context):
    """Delete all Customers and load new ones"""

    # Get a list all of the customers
    rest_endpoint = f"{context.base_url}/api/customers"
    context.resp = requests.get(rest_endpoint, timeout=WAIT_TIMEOUT)
    expect(context.resp.status_code).equal_to(HTTP_200_OK)
    
    # and delete them one by one
    for customer in context.resp.json():
        context.resp = requests.delete(
            f"{rest_endpoint}/{customer['id']}", timeout=WAIT_TIMEOUT
        )
        expect(context.resp.status_code).equal_to(HTTP_204_NO_CONTENT)

    # load the database with new customers
    for row in context.table:
        payload = {
            "first_name": row['first_name'],
            "last_name": row['last_name'],
            "address": row['address']
        }
        
        context.resp = requests.post(rest_endpoint, json=payload, timeout=WAIT_TIMEOUT)
        expect(context.resp.status_code).equal_to(HTTP_201_CREATED)
        
        # If status was provided and not 'active', update it
        if 'status' in row.headings and row['status'] != 'active':
            customer_id = context.resp.json()['id']
            status_payload = {"status": row['status']}
            context.resp = requests.put(
                f"{rest_endpoint}/{customer_id}/status",
                json=status_payload,
                timeout=WAIT_TIMEOUT
            )
            expect(context.resp.status_code).equal_to(HTTP_200_OK)


######################################################################
# Steps for clicking action buttons in the customer table
######################################################################

@when('I click the "{action}" button for "{customer_name}" in the results')
def step_impl(context, action, customer_name):
    """Click an action button (Edit, Delete, Activate, Deactivate, Suspend) for a specific customer in the table"""
    # Wait for the table to load and contain the customer
    WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.text_to_be_present_in_element(
            (By.ID, "search_results"), customer_name.split()[0]
        )
    )
    
    # Find all rows in the table
    container = context.driver.find_element(By.ID, "search_results")
    rows = container.find_elements(By.TAG_NAME, "tr")
    
    # Look for the row with this customer
    for row in rows:
        row_text = row.text
        # Check if this row contains the customer name
        name_parts = customer_name.split()
        if all(part in row_text for part in name_parts):
            # Find the action button in this row
            buttons = row.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if action.lower() in btn.text.lower():
                    btn.click()
                    return
            raise AssertionError(f"Button '{action}' not found for customer '{customer_name}'")
    
    raise AssertionError(f"Customer '{customer_name}' not found in the table")


@when('I confirm the deletion')
def step_impl(context):
    """Accept the browser confirmation dialog"""
    WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.alert_is_present()
    )
    alert = context.driver.switch_to.alert
    alert.accept()


@when('I cancel the deletion')
def step_impl(context):
    """Dismiss the browser confirmation dialog"""
    WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.alert_is_present()
    )
    alert = context.driver.switch_to.alert
    alert.dismiss()


@then('I should see "{status}" as the status for "{customer_name}" in the results')
def step_impl(context, status, customer_name):
    """Verify customer has specific status in the table"""
    import time
    time.sleep(0.5)  # Small wait for table to update
    
    # Wait for the table to contain the customer
    WebDriverWait(context.driver, context.wait_seconds).until(
        expected_conditions.text_to_be_present_in_element(
            (By.ID, "search_results"), customer_name.split()[0]
        )
    )
    
    # Find all rows in the table
    container = context.driver.find_element(By.ID, "search_results")
    rows = container.find_elements(By.TAG_NAME, "tr")
    
    # Look for the row with this customer
    for row in rows:
        row_text = row.text
        name_parts = customer_name.split()
        if all(part in row_text for part in name_parts):
            # Check if the status is in the row
            assert status.lower() in row_text.lower(), \
                f"Expected status '{status}' for {customer_name}, but row contains: {row_text}"
            return
    
    raise AssertionError(f"Customer '{customer_name}' not found in table")
