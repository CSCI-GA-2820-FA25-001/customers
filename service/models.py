"""
Models for Customer

All of the models are stored in this module
"""

import logging
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""


class Customer(db.Model):
    """
    Class that represents a Customer
    """

    ##################################################
    # Table Schema
    ##################################################
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(63))
    last_name = db.Column(db.String(63))
    address = db.Column(db.String(256))

    # Todo: Place the rest of your schema here...

    def __repr__(self):
        return f"<Customer {self.first_name} {self.last_name} id=[{self.id}]>"

    def create(self):
        """
        Creates a Customer to the database
        """
        #logger.info("Creating %s %s", self.first_name, self.last_name)
        try:
            db.session.add(self)
            db.session.commit()
            logger.info("Created Customer %s %s", self.first_name, self.last_name)
        except Exception as e:
            db.session.rollback()
            logger.error("Error creating Customer: %s", e)
            raise DataValidationError(e) from e
        return self

    def update(self):
        """
        Updates a Customer to the database
        """
        logger.info("Updating %s %s", self.first_name, self.last_name)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error updating record: %s", e)
            raise DataValidationError(e) from e
        return self

    def delete(self):
        """Removes a Customer from the data store"""
        logger.info("Deleting %s", self.name)
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error deleting record: %s", self)
            raise DataValidationError(e) from e

    def serialize(self):
        """Serializes a Customer into a dictionary"""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "address": self.address,
        }

    def deserialize(self, data):
        """
        Deserializes a Customer from a dictionary

        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            self.first_name = data["first_name"]
            self.last_name = data["last_name"]
            self.address = data.get("address", "")
        except KeyError as error:
            raise DataValidationError(f"Missing {error.args[0]}")
        return self 


    ##################################################
    # CLASS METHODS
    ##################################################

    @classmethod
    def all(cls):
        """Returns all of the Customers in the database"""
        logger.info("Processing all Customers")
        return cls.query.all()

    @classmethod
    def find(cls, by_id):
        """Finds a Customer by it's ID"""
        logger.info("Processing lookup for id %s ...", by_id)
        return cls.query.get(by_id)

    @classmethod
    def find_by_name(cls, first_name, last_name=None):
        """Finds customers by first or full name"""
        logger.info("Processing name query for %s ...", first_name)
        query = cls.query.filter(cls.first_name == first_name)
        if last_name:
            query = query.filter(cls.last_name == last_name)
        return query.all()
