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
from service import routes
from service.common import status
from service.models import db, Customer, DataValidationError
from tests.factories import CustomerFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)

BASE_URL = "/api/customers"


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
        # Check for HTML content
        self.assertIn(b"<!DOCTYPE html>", resp.data)
        self.assertIn(b"Customer Administration", resp.data)

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
        resp = self.client.get("/api/customers/9999")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_customer_invalid(self):
        """It should return 400 when creating an invalid customer"""
        resp = self.client.post("/api/customers", json={})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_customer_success(self):
        """It should return 200 and the customer payload"""
        cust = Customer(
            first_name="Aishwarya",
            last_name="Anand",
            address="12 Logic Ln",
        )
        cust.create()

        resp = self.client.get(f"/api/customers/{cust.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        for k in ("id", "first_name", "last_name", "address"):
            self.assertIn(k, data)
        self.assertEqual(data["id"], cust.id)

    def test_get_customer_not_found_message(self):
        """It should include a helpful 404 message"""
        resp = self.client.get("/api/customers/99999")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        body = resp.get_json()
        self.assertIn("customer not found", body.get("message", ""))

    def test_get_customer_non_integer_id_returns_400_json(self):
        """It should return 400 when the id is not an integer"""
        resp = self.client.get("/api/customers/abc")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertEqual(data["error"], "Bad Request")
        self.assertIn("must be an integer", data["message"])

    def test_create_customer_datavalidation_error(self):
        """It should return 400 via DataValidationError when JSON is present but invalid"""
        payload = {"first_name": "OnlyFirst"}
        resp = self.client.post("/api/customers", json=payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        body = resp.get_json()
        self.assertEqual(body.get("error"), "Bad Request")
        self.assertIn("missing last_name", body.get("message", ""))

    # ----------------------------------------------------------
    # TEST UPDATE (PUT /api/customers/{id})
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
        resp = self.client.delete(f"/api/customers/{c.id}")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        resp = self.client.get(f"/api/customers/{c.id}")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_customer_non_integer_id_returns_400(self):
        """It should return 400 Bad Request when customer_id is not an integer"""
        resp = self.client.delete("/api/customers/abcd")
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

        resp = self.client.get("/api/customers")
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
        resp = self.client.get("/api/customers")
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
        resp = self.client.post("/api/customers", json=payload)
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = resp.get_json()
        self.assertEqual(data["error"], "Internal Server Error")

        # Restore original method
        Customer.deserialize = original_deserialize

    def test_update_status_happy_path(self):
        """It should set status to a valid new value and return 200"""
        c = self._create_customers(1)[0]
        resp = self.client.put(
            f"{BASE_URL}/{c.id}/status", json={"status": "deactivated"}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        body = resp.get_json()
        self.assertEqual(body["id"], c.id)
        self.assertEqual(body["status"], "deactivated")

    def test_update_status_idempotent(self):
        """It should be idempotent (setting same status returns 200 and unchanged)"""
        c = Customer(first_name="A", last_name="B", address="X")
        c.create()
        # first set
        self.client.put(f"{BASE_URL}/{c.id}/status", json={"status": "suspended"})
        # set again to same value
        resp = self.client.put(
            f"{BASE_URL}/{c.id}/status", json={"status": "suspended"}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get_json()["status"], "suspended")

    def test_update_status_unsupported_value(self):
        """It should return 400 for unsupported status value"""
        c = self._create_customers(1)[0]
        resp = self.client.put(f"{BASE_URL}/{c.id}/status", json={"status": "frozen"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        body = resp.get_json()
        self.assertEqual(body["error"], "Bad Request")
        self.assertIn("unsupported status", body["message"])

    def test_update_status_missing_field(self):
        """It should return 400 when 'status' field is missing"""
        c = self._create_customers(1)[0]
        resp = self.client.put(f"{BASE_URL}/{c.id}/status", json={})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        body = resp.get_json()
        self.assertEqual(body["error"], "Bad Request")
        self.assertIn("status", body["message"].lower())

    def test_update_status_no_json(self):
        """It should return 400 when no JSON body is provided"""
        c = self._create_customers(1)[0]
        resp = self.client.put(
            f"{BASE_URL}/{c.id}/status", data="", content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", resp.get_json()["message"].lower())

    def test_update_status_non_integer_id(self):
        """It should return 400 when id is not an integer"""
        resp = self.client.put(f"{BASE_URL}/abc/status", json={"status": "active"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        body = resp.get_json()
        self.assertEqual(body["error"], "Bad Request")
        self.assertIn("must be an integer", body["message"])

    def test_update_status_not_found(self):
        """It should return 404 when the customer does not exist"""
        resp = self.client.put(f"{BASE_URL}/999999/status", json={"status": "active"})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("customer not found", resp.get_json().get("message", "").lower())

    def test_update_status_internal_error_during_find(self):
        """It should return 500 when an unexpected error occurs during lookup"""
        c = self._create_customers(1)[0]
        original_find = Customer.find

        def boom(_):
            raise RuntimeError("DB exploded")

        Customer.find = staticmethod(boom)
        try:
            resp = self.client.put(
                f"{BASE_URL}/{c.id}/status", json={"status": "active"}
            )
            self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(resp.get_json()["error"], "Internal Server Error")
        finally:
            Customer.find = original_find


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

    ######################################################################
    #  T E S T   QUERY CUSTOMER BY ATTRIBUTES
    ######################################################################
    def test_query_customers(self):
        """It should query customers by attribute"""
        # Create sample customers
        customer1 = CustomerFactory(first_name="Alice", last_name="Smith", address="NY")
        customer2 = CustomerFactory(first_name="Bob", last_name="Jones", address="CA")
        customer1.create()
        customer2.create()

        resp = self.client.get("/api/customers?last_name=Smith")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()

        # Check that at least one Smith exists and Alice is in the results
        smith_customers = [c for c in data if c["last_name"] == "Smith"]
        self.assertGreater(len(smith_customers), 0, "Should find at least one Smith")
        first_names = [c["first_name"] for c in smith_customers]
        self.assertIn("Alice", first_names, "Alice Smith should be in results")

    def test_query_invalid_param(self):
        """It should return 400 for invalid query param"""
        resp = self.client.get("/api/customers?invalidField=value")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_query_customers_combined_snakecase(self):
        """It should support snake_case query params and combine multiple filters with AND logic"""
        customer1 = CustomerFactory(
            first_name="John", last_name="Smith", address="Boston MA"
        )
        customer2 = CustomerFactory(
            first_name="Jane", last_name="Smith", address="New York"
        )
        customer1.create()
        customer2.create()

        resp = self.client.get("/api/customers?last_name=Smith&address=Boston")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["first_name"], "John")

    def test_query_customers_no_matches_returns_empty(self):
        """It should return an empty list when no customers match the query"""
        CustomerFactory(
            first_name="Alice", last_name="Wonder", address="Paris"
        ).create()
        resp = self.client.get("/api/customers?last_name=NonExistent")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 0)

    def test_query_customers_pagination(self):
        """It should support pagination via limit and page parameters"""
        for i in range(5):
            CustomerFactory(
                first_name=f"P{i}", last_name="Pagin", address="Addr"
            ).create()

        resp = self.client.get("/api/customers?last_name=Pagin&limit=2&page=2")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

    def test_query_id_non_integer_returns_400(self):
        """It should return 400 when query id is not an integer"""
        CustomerFactory(first_name="Z", last_name="Q", address="X").create()
        resp = self.client.get("/api/customers?id=abc")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertEqual(data.get("error"), "Bad Request")
        self.assertIn("id must be an integer", data.get("message", ""))

    def test_query_limit_non_integer_returns_400(self):
        """It should return 400 when limit is not an integer"""
        CustomerFactory(first_name="L", last_name="M", address="N").create()
        resp = self.client.get("/api/customers?limit=abc")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertEqual(data.get("error"), "Bad Request")
        self.assertIn("limit must be an integer", data.get("message", ""))

    def test_query_limit_non_positive_returns_400(self):
        """It should return 400 when limit is not a positive integer"""
        for i in range(3):
            CustomerFactory(
                first_name=f"N{i}", last_name="Pos", address="Addr"
            ).create()
        resp = self.client.get("/api/customers?limit=0&page=1")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.get_json()
        self.assertEqual(data.get("error"), "Bad Request")
        self.assertIn("limit must be a positive integer", data.get("message", ""))

    ######################################################################
    #  T E S T   H E A L T H  E N D P O I N T
    ######################################################################
    def test_health_endpoint(self):
        """It should return 200 OK with status 'OK'"""
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")


######################################################################
#  T E S T   R E S T X   W R A P P E R S   A N D   E R R O R S
######################################################################


def test_restx_get_customers(client=app.test_client()):
    """Covers CustomerListAPI.get() RESTX endpoint"""
    resp = client.get("/api/customers/")
    assert resp.status_code == 200


def test_restx_create_customer(client=app.test_client()):
    """Covers CustomerListAPI.post() RESTX endpoint"""
    payload = {"first_name": "RestX", "last_name": "Test", "address": "SlashCity"}
    resp = client.post("/api/customers/", json=payload)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["first_name"] == "RestX"


def test_restx_unexpected_exception(monkeypatch, client=app.test_client()):
    """Covers app.logger.exception(...) in RESTX error handler"""

    def boom():
        raise RuntimeError("Simulated crash")

    monkeypatch.setattr(routes, "list_customers", boom)
    resp = client.get("/api/customers/")
    assert resp.status_code == 500
    data = resp.get_json()
    assert data["error"] == "Internal Server Error"
