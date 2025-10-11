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
Customer Service

This service implements a REST API that allows you to Create, Read, Update
and Delete Customer
"""

from flask import jsonify, request
from flask import current_app as app  # Import Flask application
from werkzeug.exceptions import NotFound, BadRequest, InternalServerError

from service.models import Customer, DataValidationError
from service.common import status  # HTTP Status Codes


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        jsonify(
            {
                "name": "Customers Service",
                "version": "v1.0.0",
                "description": "Service managing customer accounts for the eCommerce site",
                "list_url": "/customers",
            }
        ),
        status.HTTP_200_OK,
    )


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################

@app.route("/customers", methods=["POST"])
def create_customer():
    """Creates a new Customer record"""
    data = request.get_json()
    if not data:
        raise BadRequest("No input data provided")

    try:
        customer = Customer().deserialize(data)
        customer.create()
        return jsonify(customer.serialize()), status.HTTP_201_CREATED
    except DataValidationError as e:
        app.logger.error("Data validation error: %s", e)
        raise BadRequest(str(e)) from e
    except Exception as e:
        app.logger.exception("Unexpected error creating customer")
        raise InternalServerError(str(e)) from e


@app.route("/customers/<customer_id>", methods=["GET"])
def get_customer(customer_id):
    """Read a single customer by id"""
    if not customer_id.isdigit():
        raise BadRequest("customer id must be an integer")
    customer_id = int(customer_id)

    try:
        customer = Customer.find(customer_id)
    except Exception as err:  # pragma: no cover - unexpected
        app.logger.exception("Unexpected error reading customer %s", customer_id)
        raise InternalServerError(str(err)) from err

    if not customer:
        raise NotFound("customer not found")

    return jsonify(customer.serialize()), status.HTTP_200_OK


@app.route("/customers", methods=["GET"])
def list_customers():
    """Returns a list of all Customers"""
    app.logger.info("Request to list all customers")
    try:
        customers = Customer.query.all()
        results = [customer.serialize() for customer in customers]
        return jsonify(results), status.HTTP_200_OK
    except Exception as e:
        app.logger.exception("Error fetching customers: %s", e)
        raise InternalServerError(str(e)) from e


@app.route("/customers/<customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    """Delete a customer by id"""
    if not customer_id.isdigit():
        raise BadRequest("customer id must be an integer")
    customer_id = int(customer_id)

    try:
        customer = Customer.find(customer_id)
    except Exception as err:
        app.logger.exception("Unexpected error locating customer %s", customer_id)
        raise InternalServerError(str(err)) from err

    if not customer:
        raise NotFound("customer not found")

    try:
        customer.delete()
    except DataValidationError as err:
        app.logger.exception("Unexpected error deleting customer %s", customer_id)
        raise InternalServerError(str(err)) from err

    return "", status.HTTP_204_NO_CONTENT
