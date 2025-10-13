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
TestCustomer API Service Test Suite
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from wsgi import app
from service.common import status
from service.models import db, Customer
from tests.factories import CustomerFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)

BASE_URL = "/customers"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestYourResourceService(TestCase):
    """REST API Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Customer).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ############################################################
    # Utility function to bulk create customers
    ############################################################
    def _create_customers(self, count: int = 1) -> list:
        """Factory method to create customers in bulk"""
        customers = []
        for _ in range(count):
            test_customer = CustomerFactory()
            response = self.client.post(BASE_URL, json=test_customer.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test customer",
            )
            new_customer = response.get_json()
            test_customer.id = new_customer["id"]
            customers.append(test_customer)
        return customers

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should call the home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["name"], "Customers Service")

    # ----------------------------------------------------------
    # TEST READ
    # ----------------------------------------------------------

    def test_get_customer_list(self):
        """It should Get a list of Customers"""
        self._create_customers(5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 5)

    def test_get_customer_not_found(self):
        """It should return 404 if customer is not found"""
        resp = self.client.get("/customers/9999")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_customer_invalid(self):
        """It should return 400 when creating an invalid customer"""
        resp = self.client.post("/customers", json={})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_customer_success(self):
        """It should return 200 and the customer payload"""
        cust = Customer(
            first_name="Aishwarya",
            last_name="Anand",
            address="12 Logic Ln",
        )
        cust.create()

        resp = self.client.get(f"/customers/{cust.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        for k in ("id", "first_name", "last_name", "address"):
            self.assertIn(k, data)
        self.assertEqual(data["id"], cust.id)

    def test_get_customer_not_found_message(self):
        """It should include a helpful 404 message"""
        resp = self.client.get("/customers/99999")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        body = resp.get_json()
        self.assertIn("customer not found", body.get("message", ""))

    def test_get_customer_non_integer_id_returns_400_json(self):
        """It should return 400 when the id is not an integer"""
        resp = self.client.get("/customers/abc")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertEqual(data["error"], "Bad Request")
        self.assertIn("must be an integer", data["message"])

    def test_create_customer_datavalidation_error(self):
        """It should return 400 via DataValidationError when JSON is present but invalid"""
        payload = {"first_name": "OnlyFirst"}
        resp = self.client.post("/customers", json=payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        body = resp.get_json()
        self.assertEqual(body.get("error"), "Bad Request")
        self.assertIn("missing last_name", body.get("message", ""))

    # ----------------------------------------------------------
    # TEST UPDATE (PUT /customers/{id})
    # ----------------------------------------------------------

    def test_update_customer_success(self):
        """It should update an existing customer and return 200 with updated JSON"""
        customer = self._create_customers(1)[0]
        cust_id = customer.id

        payload = {
            "first_name": "UpdatedFirst",
            "last_name": "UpdatedLast",
            "address": "987 New Address Ave",
        }
        resp = self.client.put(f"{BASE_URL}/{cust_id}", json=payload)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["id"], cust_id)
        self.assertEqual(data["first_name"], payload["first_name"])
        self.assertEqual(data["last_name"], payload["last_name"])
        self.assertEqual(data["address"], payload["address"])

        resp_get = self.client.get(f"{BASE_URL}/{cust_id}")
        self.assertEqual(resp_get.status_code, status.HTTP_200_OK)
        persisted = resp_get.get_json()
        self.assertEqual(persisted["first_name"], "UpdatedFirst")
        self.assertEqual(persisted["last_name"], "UpdatedLast")
        self.assertEqual(persisted["address"], "987 New Address Ave")

    def test_update_customer_partial_fields(self):
        """It should allow updating only provided fields (e.g., just address)"""
        customer = self._create_customers(1)[0]
        cust_id = customer.id
        original_first = customer.first_name
        original_last = customer.last_name

        payload = {"address": "42 Galaxy Way"}
        resp = self.client.put(f"{BASE_URL}/{cust_id}", json=payload)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["first_name"], original_first)
        self.assertEqual(data["last_name"], original_last)
        self.assertEqual(data["address"], "42 Galaxy Way")

    def test_update_customer_not_found(self):
        """It should return 404 when the customer does not exist"""
        payload = {"first_name": "Nobody", "last_name": "Home", "address": "N/A"}
        resp = self.client.put(f"{BASE_URL}/99999", json=payload)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        body = resp.get_json()
        self.assertIn("customer not found", body.get("message", "").lower())

    def test_update_customer_invalid_data_whitespace(self):
        """It should return 400 when provided fields are empty after trimming"""
        customer = self._create_customers(1)[0]
        cust_id = customer.id

        payload = {"address": "   "}
        resp = self.client.put(f"{BASE_URL}/{cust_id}", json=payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertEqual(data.get("error"), "Bad Request")
        self.assertIn("address", data.get("message", "").lower())

    def test_update_customer_reject_id_update(self):
        """It should not allow updating the id field"""
        customer = self._create_customers(1)[0]
        cust_id = customer.id

        payload = {
            "id": cust_id + 1,
            "first_name": "X",
            "last_name": "Y",
            "address": "Z",
        }
        resp = self.client.put(f"{BASE_URL}/{cust_id}", json=payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertEqual(data.get("error"), "Bad Request")
        self.assertIn("id", data.get("message", "").lower())

    def test_update_customer_non_integer_id_returns_400(self):
        """It should return 400 Bad Request when customer_id is not an integer"""
        payload = {"first_name": "Foo", "last_name": "Bar", "address": "Baz"}
        resp = self.client.put(f"{BASE_URL}/abc", json=payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertEqual(data["error"], "Bad Request")
        self.assertIn("must be an integer", data["message"])

    def test_update_customer_with_exception(self):
        """It should return 500 when an unexpected exception occurs during update"""

        def mock_deserialize(_self, data):
            raise RuntimeError("Unexpected error during update")

        customer = self._create_customers(1)[0]
        cust_id = customer.id

        original_deserialize = Customer.deserialize
        Customer.deserialize = mock_deserialize

        try:
            payload = {"first_name": "Boom", "last_name": "Crash", "address": "Bang"}
            resp = self.client.put(f"{BASE_URL}/{cust_id}", json=payload)
            self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            data = resp.get_json()
            self.assertEqual(data["error"], "Internal Server Error")
        finally:
            Customer.deserialize = original_deserialize

    def test_update_customer_no_input_data_returns_400(self):
        """It should return 400 when no input data is provided"""
        c = self._create_customers(1)[0]
        resp = self.client.put(
            f"{BASE_URL}/{c.id}", data="", content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertIn("No input data provided", data["message"])

    def test_update_customer_no_updatable_fields_returns_existing(self):
        """It should return existing record when no updatable fields are given"""
        c = self._create_customers(1)[0]
        resp = self.client.put(f"{BASE_URL}/{c.id}", json={})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["id"], c.id)
        self.assertEqual(data["first_name"], c.first_name)
        self.assertEqual(data["last_name"], c.last_name)
        self.assertEqual(data["address"], c.address)

    def test_update_customer_find_raises_exception_returns_500(self):
        """It should return 500 when Customer.find raises an unexpected exception"""
        c = self._create_customers(1)[0]
        original_find = Customer.find

        def boom(_):
            raise RuntimeError("DB exploded")

        Customer.find = staticmethod(boom)
        try:
            payload = {"first_name": "A", "last_name": "B", "address": "C"}
            resp = self.client.put(f"{BASE_URL}/{c.id}", json=payload)
            self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(resp.get_json()["error"], "Internal Server Error")
        finally:
            Customer.find = original_find

    def test_update_customer_datavalidation_error_returns_400(self):
        """It should return 400 when a DataValidationError occurs during update"""
        from service.models import DataValidationError

        c = self._create_customers(1)[0]
        original_deserialize = Customer.deserialize

        def bad_deserialize(self, data):
            raise DataValidationError("bad data in update")

        Customer.deserialize = bad_deserialize
        try:
            payload = {"first_name": "X", "last_name": "Y", "address": "Z"}
            resp = self.client.put(f"{BASE_URL}/{c.id}", json=payload)
            self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("bad data", resp.get_json()["message"])
        finally:
            Customer.deserialize = original_deserialize

    # ----------------------------------------------------------
    # TEST DELETE
    # ----------------------------------------------------------

    def test_delete_customer(self):
        """It should Delete a Customer"""
        test_customer = self._create_customers(1)[0]
        response = self.client.delete(f"{BASE_URL}/{test_customer.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)
        # make sure they are deleted
        response = self.client.get(f"{BASE_URL}/{test_customer.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_non_existing_customer(self):
        """It should Delete a Customer even if it doesn't exist"""
        response = self.client.delete(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)

    def test_delete_customer_success(self):
        """It should delete an existing customer and return 204"""
        c = Customer(first_name="Aishwarya", last_name="Anand", address="nyu")
        c.create()
        resp = self.client.delete(f"/customers/{c.id}")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        resp = self.client.get(f"/customers/{c.id}")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_customer_non_integer_id_returns_400(self):
        """It should return 400 Bad Request when customer_id is not an integer"""
        resp = self.client.delete("/customers/abcd")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertEqual(data["error"], "Bad Request")
        self.assertIn("must be an integer", data["message"])

    def test_list_customers_success(self):
        """It should successfully list all customers"""
        c1 = Customer(first_name="Alice", last_name="Smith", address="123 Main St")
        c2 = Customer(first_name="Bob", last_name="Jones", address="456 Elm St")
        c1.create()
        c2.create()

        resp = self.client.get("/customers")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 2)
        first_names = [c["first_name"] for c in data]
        self.assertIn("Alice", first_names)
        self.assertIn("Bob", first_names)

    def test_list_customers_internal_error(self):
        """It should handle internal server errors when listing customers"""

        # pylint: disable=too-few-public-methods
        class MockQuery:
            """Class for database failures"""

            def all(self):
                """Raises exception for database failures"""
                raise RuntimeError("Database failure")

        original_query = Customer.query
        Customer.query = MockQuery()
        resp = self.client.get("/customers")
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = resp.get_json()
        self.assertIn("Internal Server Error", data["error"])
        Customer.query = original_query

    def test_create_customer_with_exception(self):
        """It should return 500 when an unexpected exception occurs during creation"""

        def mock_deserialize(_):
            raise RuntimeError("Unexpected error")

        original_deserialize = Customer.deserialize
        Customer.deserialize = mock_deserialize

        payload = {"first_name": "Error", "last_name": "Case", "address": "Test"}
        resp = self.client.post("/customers", json=payload)
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = resp.get_json()
        self.assertEqual(data["error"], "Internal Server Error")

        # Restore original method
        Customer.deserialize = original_deserialize


######################################################################
#  T E S T   S A D   P A T H S
######################################################################


class TestSadPaths(TestCase):
    """Test REST Exception Handling"""

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()

    def test_method_not_allowed(self):
        """It should not allow update without a customer id"""
        response = self.client.put(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_create_customer_no_data(self):
        """It should not Create a Customer with missing data"""
        response = self.client.post(BASE_URL, json={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_customer_no_content_type(self):
        """It should not Create a Customer with no content type"""
        response = self.client.post(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_customer_wrong_content_type(self):
        """It should not Create a Customer with the wrong content type"""
        response = self.client.post(BASE_URL, data="hello", content_type="text/html")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
