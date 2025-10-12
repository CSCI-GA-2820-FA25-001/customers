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

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


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

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should call the home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

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
        self.assertIn("Missing last_name", body.get("message", ""))

    def test_delete_customer_success(self):
        """It should delete an existing customer and return 204"""
        c = Customer(first_name="Aishwarya", last_name="Anand", address="nyu")
        c.create()
        resp = self.client.delete(f"/customers/{c.id}")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        resp = self.client.get(f"/customers/{c.id}")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_customer_not_found(self):
        """It should return 404 for a non-existent customer"""
        resp = self.client.delete("/customers/99999")
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
                raise Exception("Database failure") # pylint: disable=broad-exception-raised
        original_query = Customer.query
        Customer.query = MockQuery()  # Replace the entire query object
        resp = self.client.get("/customers")
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = resp.get_json()
        self.assertIn("Internal Server Error", data["error"])
        Customer.query = original_query
    def test_create_customer_with_exception(self):
        """It should return 500 when an unexpected exception occurs during creation"""
        # Monkeypatch Customer.deserialize to raise a general Exception
        def mock_deserialize(_):
            raise Exception("Unexpected error")  # pylint: disable=broad-exception-raised

        original_deserialize = Customer.deserialize
        Customer.deserialize = mock_deserialize

        payload = {"first_name": "Error", "last_name": "Case", "address": "Test"}
        resp = self.client.post("/customers", json=payload)
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = resp.get_json()
        self.assertEqual(data["error"], "Internal Server Error")

        # Restore original method
        Customer.deserialize = original_deserialize
