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
Test cases for Pet Model
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
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

    # Todo: Add your test cases here...
    def test_list_all_customers(app):
     """It should list all Customers"""
    with app.app_context():
        # Clear all existing customers
        db.session.query(Customer).delete()
        db.session.commit()

        # Add multiple customers
        customer1 = Customer(first_name="Alice", last_name="Smith", address="123 Main St")
        customer2 = Customer(first_name="Bob", last_name="Johnson", address="456 Elm St")
        customer3 = Customer(first_name="Carol", last_name="Williams", address="789 Oak St")

        db.session.add_all([customer1, customer2, customer3])
        db.session.commit()

        # Fetch all customers using class method
        customers = Customer.all()
        assert len(customers) == 3
        names = [c.first_name for c in customers]
        assert "Alice" in names
        assert "Bob" in names
        assert "Carol" in names
        
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

    def test_repr(self):
        """It should return a string representation of the Customer"""
        customer = CustomerFactory()
        result = repr(customer)
        self.assertIn("Customer", result)