######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
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
Test cases for Customer Model
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from unittest.mock import patch, PropertyMock  # ← Move this line here

from wsgi import app
from service.models import Customer, DataValidationError, db
from .factories import CustomerFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  C U S T O M E R  M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestCustomer(TestCase):
    """Test Cases for Customer Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Customer).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_customer(self):
        """It should create a Customer"""
        customer = CustomerFactory()
        customer.create()
        self.assertIsNotNone(customer.id)
        found = Customer.all()
        self.assertEqual(len(found), 1)
        data = Customer.find(customer.id)
        self.assertEqual(data.first_name, customer.first_name)
        self.assertEqual(data.last_name, customer.last_name)
        self.assertEqual(data.address, customer.address)

    def test_create_customer_with_database_error(self):
        """It should handle database errors during create"""
        customer = CustomerFactory()
        # Force a database error by trying to add duplicate primary key
        customer.id = 1
        customer.create()

        # Try to create another with same ID
        duplicate = CustomerFactory()
        duplicate.id = 1
        with self.assertRaises(DataValidationError):
            duplicate.create()

    def test_add_a_customer(self):
        """It should Create a customer and add it to the database"""
        customers = Customer.all()
        self.assertEqual(customers, [])
        customer = Customer(
            first_name="John",
            last_name="Doe",
            address="123 Main Street, New York, NY 10001",
        )
        self.assertTrue(customer is not None)
        self.assertEqual(customer.id, None)
        customer.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(customer.id)
        customers = Customer.all()
        self.assertEqual(len(customers), 1)

    def test_read_a_customer(self):
        """It should Read a Customer"""
        customer = CustomerFactory()
        logging.debug(customer)
        customer.id = None
        customer.create()
        self.assertIsNotNone(customer.id)
        # Fetch it back
        found_customer = Customer.find(customer.id)
        self.assertEqual(found_customer.id, customer.id)
        self.assertEqual(found_customer.first_name, customer.first_name)
        self.assertEqual(found_customer.last_name, customer.last_name)
        self.assertEqual(found_customer.address, customer.address)

    def test_list_all_customers(self):
        """It should list all Customers"""
        # Add multiple customers with deterministic names
        c1 = Customer(first_name="Alice", last_name="Smith", address="123 Main St")
        c2 = Customer(first_name="Bob", last_name="Johnson", address="456 Elm St")
        c3 = Customer(first_name="Carol", last_name="Williams", address="789 Oak St")
        for c in (c1, c2, c3):
            c.create()

        customers = Customer.all()
        self.assertEqual(len(customers), 3)
        names = {c.first_name for c in customers}
        self.assertTrue({"Alice", "Bob", "Carol"}.issubset(names))

    def test_serialize_customer(self):
        """It should serialize a Customer into a dictionary"""
        customer = CustomerFactory()
        data = customer.serialize()
        self.assertIn("first_name", data)
        self.assertIn("last_name", data)
        self.assertIn("address", data)
        self.assertEqual(data["first_name"], customer.first_name)

    def test_deserialize_customer(self):
        """It should deserialize a Customer from a dictionary"""
        data = {
            "first_name": "Arushi",
            "last_name": "Srivastava",
            "address": "123 Main Street",
        }
        customer = Customer()
        customer.deserialize(data)
        self.assertEqual(customer.first_name, "Arushi")
        self.assertEqual(customer.last_name, "Srivastava")
        self.assertEqual(customer.address, "123 Main Street")

    def test_deserialize_missing_data(self):
        """It should raise DataValidationError when required fields are missing"""
        data = {"first_name": "Alex"}
        customer = Customer()
        with self.assertRaises(DataValidationError):
            customer.deserialize(data)

    def test_deserialize_bad_data(self):
        """It should not deserialize bad data"""
        data = "this is not a dictionary"
        customer = Customer()
        self.assertRaises(DataValidationError, customer.deserialize, data)

    def test_repr(self):
        """It should return a string representation of the Customer"""
        customer = CustomerFactory()
        result = repr(customer)
        self.assertIn("Customer", result)

    def test_update_customer(self):
        """It should update an existing Customer"""
        customer = CustomerFactory()
        customer.create()
        old_id = customer.id
        customer.address = "999 Maple Ave"
        customer.update()

        updated = Customer.find(old_id)
        self.assertEqual(updated.address, "999 Maple Ave")

    def test_update_no_id(self):
        """It should not Update a Customer with no id"""
        customer = CustomerFactory()
        logging.debug(customer)
        customer.id = None
        self.assertRaises(DataValidationError, customer.update)

    def test_delete_customer(self):
        """It should delete a Customer"""
        customer = CustomerFactory()
        customer.create()
        customer_id = customer.id
        customer.delete()
        self.assertIsNone(Customer.find(customer_id))

    def test_delete_customer_with_database_error(self):
        """It should handle database errors during delete"""

        customer = CustomerFactory()
        customer.create()

        # Mock db.session.delete to raise an exception
        with patch("service.models.db.session.delete") as mock_delete:
            mock_delete.side_effect = Exception("Database error")
            with self.assertRaises(DataValidationError):
                customer.delete()

    def test_find_customer_not_found(self):
        """It should return None if the Customer is not found"""
        self.assertIsNone(Customer.find(999999))

    def test_deserialize_with_invalid_data(self):
        """It should raise DataValidationError for invalid data types"""
        customer = Customer()
        bad_data = {"first_name": 123, "last_name": True, "address": None}
        with self.assertRaises(DataValidationError):
            customer.deserialize(bad_data)

    def test_deserialize_with_invalid_first_name_type(self):
        """It should raise DataValidationError for invalid first_name type"""
        customer = Customer()
        bad_data = {"first_name": 123, "last_name": "Doe", "address": "123 Main St"}
        with self.assertRaises(DataValidationError) as context:
            customer.deserialize(bad_data)
        self.assertIn("first_name", str(context.exception))

    def test_deserialize_with_invalid_last_name_type(self):
        """It should raise DataValidationError for invalid last_name type"""
        customer = Customer()
        bad_data = {"first_name": "John", "last_name": True, "address": "123 Main St"}
        with self.assertRaises(DataValidationError) as context:
            customer.deserialize(bad_data)
        self.assertIn("last_name", str(context.exception))

    def test_deserialize_with_invalid_address_type(self):
        """It should raise DataValidationError for invalid address type"""
        customer = Customer()
        bad_data = {"first_name": "John", "last_name": "Doe", "address": None}
        with self.assertRaises(DataValidationError) as context:
            customer.deserialize(bad_data)
        self.assertIn("address", str(context.exception))

    def test_deserialize_with_attribute_error(self):
        """It should raise DataValidationError on AttributeError"""
        customer = Customer()
        # Mock to cause AttributeError

        with patch.object(
            Customer, "first_name", new_callable=PropertyMock
        ) as mock_prop:
            mock_prop.side_effect = AttributeError("test error")
            with self.assertRaises(DataValidationError):
                customer.deserialize(
                    {"first_name": "John", "last_name": "Doe", "address": "123 Main"}
                )


######################################################################
#  Q U E R Y   T E S T   C A S E S
######################################################################
class TestModelQueries(TestCustomer):
    """Customer Model Query Tests"""

    def test_find_customer(self):
        """It should find a Customer by ID"""
        customers = CustomerFactory.create_batch(2)
        for customer in customers:
            customer.create()

        found = Customer.find(customers[0].id)
        self.assertIsNotNone(found)
        self.assertEqual(found.id, customers[0].id)

    def test_find_by_name(self):
        """It should find customers by name"""
        customer1 = CustomerFactory(first_name="Arushi", last_name="Srivastava")
        customer2 = CustomerFactory(first_name="Alex", last_name="Chen")
        customer1.create()
        customer2.create()

        results = Customer.find_by_name("Arushi")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].first_name, "Arushi")

    def test_find_by_name_with_last_name(self):
        """It should find customers by first and last name"""
        customer1 = CustomerFactory(first_name="John", last_name="Smith")
        customer2 = CustomerFactory(first_name="John", last_name="Doe")
        customer1.create()
        customer2.create()

        results = Customer.find_by_name("John", "Smith")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].last_name, "Smith")

    def test_find_by_address(self):
        """It should Find Customers by Address"""
        customers = CustomerFactory.create_batch(10)
        for customer in customers:
            customer.create()
        address = customers[0].address
        count = len([customer for customer in customers if customer.address == address])
        found = Customer.find_by_address(address)
        self.assertEqual(found.count(), count)
        for customer in found:
            self.assertEqual(customer.address, address)
