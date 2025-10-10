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

from flask import jsonify, request, url_for, abort
from flask import current_app as app  # Import Flask application
from service.models import Customer
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

# Todo: Place your REST API code here ...
@app.route("/customers", methods=["POST"])
def create_customer():
    """Creates a new Customer record"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request", "message": "No input data provided"}), 400

    try:
        customer = Customer().deserialize(data)  # must be an instance
        customer.create()
        return jsonify(customer.serialize()), 201
    except DataValidationError as e:
        app.logger.error("Data validation error: %s", e)
        return jsonify({"error": "Invalid customer data", "message": str(e)}), 400
    except Exception as e:
        app.logger.exception("Unexpected error creating customer")
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500


#Error handlers
@app.errorhandler(status.HTTP_400_BAD_REQUEST)
def bad_request(error):
    """Handles 400 Bad Request errors"""
    return jsonify(status=400, error="Bad Request", message=str(error)), status.HTTP_400_BAD_REQUEST


@app.errorhandler(status.HTTP_404_NOT_FOUND)
def not_found(error):
    """Handles 404 Not Found errors"""
    return jsonify(status=404, error="Not Found", message=str(error)), status.HTTP_404_NOT_FOUND


@app.errorhandler(status.HTTP_500_INTERNAL_SERVER_ERROR)
def internal_server_error(error):
    """Handles 500 Internal Server Error"""
    return (
        jsonify(status=500, error="Internal Server Error", message=str(error)),
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )