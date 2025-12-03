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
from flask_restx import Api, Namespace, Resource, fields
from service.models import Customer, DataValidationError, ALLOWED_STATUSES
from service.common import status  # HTTP Status Codes

######################################################################
# RESTX API (ADDED SAFELY)
######################################################################

restx_api = Api(
    app,
    version="1.0.0",
    title="Customers REST API Service",
    description="REST API service for managing customers",
    default="customers",
    default_label="Customer operations",
    doc="/apidocs",
    prefix="/api",
)
######################################################################
# Swagger Models
######################################################################

customer_model = restx_api.model(
    "Customer",
    {
        "first_name": fields.String(description="First Name"),
        "last_name": fields.String(description="Last Name"),
        "address": fields.String(description="Address"),
        "status": fields.String(description="Status"),
    },
)

customer_response_model = restx_api.inherit(
    "CustomerResponse",
    customer_model,
    {"id": fields.Integer(readOnly=True, description="Customer ID")},
)

status_update_model = restx_api.model(
    "StatusUpdate", {"status": fields.String(required=True, description="New status")}
)
######################################################################
# INDEX AND HEALTH
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
                "list_url": "/api/customers",
            }
        ),
        status.HTTP_200_OK,
    )


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint for Kubernetes"""
    return jsonify({"status": "OK"}), status.HTTP_200_OK


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


@app.route("/api/customers", methods=["POST"])
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
    except Exception as e:  # pragma: no cover - unexpected guard
        app.logger.exception("Unexpected error creating customer")
        raise InternalServerError(str(e)) from e


@app.route("/api/customers/<customer_id>", methods=["GET"])
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


@app.route("/api/customers", methods=["GET"])
def list_customers():
    """Returns a list of all customers
    Example queries:
      GET /api/customers
      GET /api/customers?last_name=Smith
      GET /api/customers?first_name=Alice&address=NY
    """
    # pylint: disable=broad-exception-caught
    try:
        query_params = request.args

        if not query_params:
            customers = Customer.all()
        else:
            # Validate and build filters
            allowed_fields = {"first_name", "last_name", "address", "id"}

            # Pagination params
            limit = None
            page = None

            filters = {}

            for key, value in query_params.items():
                if key in ("limit", "page"):
                    try:
                        if key == "limit":
                            limit = int(value)
                        else:
                            page = int(value)
                    except ValueError as exc:
                        raise BadRequest(f"{key} must be an integer") from exc
                    continue

                if key not in allowed_fields:
                    raise BadRequest(f"Invalid query parameter: {key}")
                filters[key] = value

            query = Customer.query
            for attr, val in filters.items():
                column = getattr(Customer, attr)
                if attr == "id":
                    try:
                        query = query.filter(column == int(val))
                    except ValueError as exc:
                        raise BadRequest("id must be an integer") from exc
                else:
                    query = query.filter(column.ilike(f"%{val}%"))

            if limit is not None:
                if limit <= 0:
                    raise BadRequest("limit must be a positive integer")
                if page is None or page <= 0:
                    page = 1
                offset = (page - 1) * limit
                customers = query.offset(offset).limit(limit).all()
            else:
                customers = query.all()

        results = [customer.serialize() for customer in customers]
        return jsonify(results), status.HTTP_200_OK

    except BadRequest as e:
        raise e
    except Exception as e:  # pragma: no cover - unexpected guard
        app.logger.error("Unexpected error while listing customers: %s", e)
        raise InternalServerError(str(e)) from e


@app.route("/api/customers/<customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    """Delete a customer by id"""
    if not customer_id.isdigit():
        raise BadRequest("customer id must be an integer")
    customer_id = int(customer_id)

    try:
        customer = Customer.find(customer_id)
    except Exception as err:  # pragma: no cover - unexpected guard
        app.logger.exception("Unexpected error locating customer %s", customer_id)
        raise InternalServerError(str(err)) from err

    if customer:
        try:
            customer.delete()
        except DataValidationError as err:  # pragma: no cover - unexpected guard
            app.logger.exception("Unexpected error deleting customer %s", customer_id)
            raise InternalServerError(str(err)) from err

    return "", status.HTTP_204_NO_CONTENT


######################################################################
# UPDATE A CUSTOMER
######################################################################
@app.route("/api/customers/<customer_id>", methods=["PUT"])
def update_customer(customer_id):  # noqa: C901
    """Update an existing Customer record by id.

    Updatable fields: first_name, last_name, address
    - All provided fields must be non-empty strings after trimming whitespace
    - The 'id' field cannot be updated
    - Partial updates are allowed (only provided fields are changed)
    """
    # pylint: disable=too-many-branches
    if not str(customer_id).isdigit():
        raise BadRequest("customer id must be an integer")
    customer_id = int(customer_id)

    try:
        data = request.get_json()
    except BadRequest as e:
        raise BadRequest("No input data provided") from e

    if data is None:
        raise BadRequest("No input data provided")

    if "id" in data:
        raise BadRequest("id cannot be updated")

    allowed_fields = {"first_name", "last_name", "address"}
    incoming = {k: v for k, v in data.items() if k in allowed_fields}

    if not incoming:
        customer = Customer.find(customer_id)
        if not customer:
            raise NotFound("customer not found")
        return jsonify(customer.serialize()), status.HTTP_200_OK

    invalid_fields = []
    cleaned = {}
    for key, value in incoming.items():
        if not isinstance(value, str) or not value.strip():
            invalid_fields.append(key)
        else:
            cleaned[key] = value.strip()

    if invalid_fields:
        raise BadRequest(
            f"invalid or empty fields: {', '.join(sorted(invalid_fields))}"
        )

    try:
        customer = Customer.find(customer_id)
    except Exception as err:  # pragma: no cover - unexpected guard
        app.logger.exception("Unexpected error locating customer %s", customer_id)
        raise InternalServerError(str(err)) from err

    if not customer:
        raise NotFound("customer not found")

    try:
        current = customer.serialize()
        current.update(cleaned)
        customer.deserialize(current)
        customer.update()
        return jsonify(customer.serialize()), status.HTTP_200_OK

    except DataValidationError as e:
        app.logger.error("Data validation error during update: %s", e)
        raise BadRequest(str(e)) from e
    except Exception as e:  # pragma: no cover - unexpected guard
        app.logger.exception("Unexpected error updating customer %s", customer_id)
        raise InternalServerError(str(e)) from e


@app.route("/api/customers/<customer_id>/status", methods=["PUT"])
def update_status(customer_id):  # noqa: C901
    """Set customer's status to one of: active | deactivated | suspended"""
    # pylint: disable=too-many-branches
    if not customer_id.isdigit():
        raise BadRequest("customer id must be an integer")
    customer_id = int(customer_id)

    data = request.get_json(silent=True)
    if not data or "status" not in data:
        raise BadRequest("Request must include a 'status' field")

    new_status = (data["status"] or "").strip().lower()
    if new_status not in ALLOWED_STATUSES:
        valid = ", ".join(sorted(ALLOWED_STATUSES))
        raise BadRequest(f"unsupported status '{new_status}'. valid statuses: {valid}")

    try:
        customer = Customer.find(customer_id)
    except Exception as err:  # pragma: no cover - unexpected guard
        app.logger.exception("Unexpected error retrieving customer %s", customer_id)
        raise InternalServerError(str(err)) from err

    if not customer:
        raise NotFound("customer not found")

    try:
        if customer.status != new_status:
            customer.set_status(new_status)
            customer.update()
        app.logger.info(
            "Status set for customer %s -> '%s'", customer_id, customer.status
        )
        return jsonify(customer.serialize()), status.HTTP_200_OK
    except DataValidationError as e:
        app.logger.error("Validation error setting status for %s: %s", customer_id, e)
        raise BadRequest(str(e)) from e
    except Exception as err:  # pragma: no cover - unexpected guard
        app.logger.exception("Unexpected error setting status for %s", customer_id)
        raise InternalServerError(str(err)) from err


######################################################################
# RESTX NAMESPACE (ONLY WRAPPERS — DO NOT AFFECT TESTS)
######################################################################

ns = Namespace("customers", description="Customer operations")


@ns.route("/")
class CustomerListAPI(Resource):
    @ns.marshal_list_with(customer_response_model)
    def get(self):
        # Call Flask route → unpack (json, code)
        flask_resp, code = list_customers()
        return flask_resp.get_json()

    @ns.expect(customer_model)
    @ns.marshal_with(customer_response_model, code=201)
    def post(self):
        flask_resp, code = create_customer()
        return flask_resp.get_json(), 201


@ns.route("/<int:customer_id>")
class CustomerAPI(Resource):
    @ns.marshal_with(customer_response_model)
    def get(self, customer_id):
        flask_resp, code = get_customer(str(customer_id))
        return flask_resp.get_json(), code

    @ns.expect(customer_model)
    @ns.marshal_with(customer_response_model)
    def put(self, customer_id):
        flask_resp, code = update_customer(str(customer_id))
        return flask_resp.get_json(), code

    def delete(self, customer_id):
        _, code = delete_customer(str(customer_id))
        return "", code


@ns.route("/<int:customer_id>/status")
class StatusAPI(Resource):
    @ns.expect(status_update_model)
    @ns.marshal_with(customer_response_model)
    def put(self, customer_id):
        flask_resp, code = update_status(str(customer_id))
        return flask_resp.get_json(), code


restx_api.add_namespace(ns)

######################################################################
#  J S O N   E R R O R   H A N D L E R S (BIND TO RESTX API)
######################################################################


@restx_api.errorhandler(BadRequest)
def handle_bad_request(error):
    """Return JSON for HTTP 400 errors"""
    app.logger.error("400 Bad Request: %s", error)
    return {"error": "Bad Request", "message": str(error)}, status.HTTP_400_BAD_REQUEST


@restx_api.errorhandler(NotFound)
def handle_not_found(error):
    """Return JSON for HTTP 404 errors"""
    app.logger.error("404 Not Found: %s", error)
    return {"error": "Not Found", "message": str(error)}, status.HTTP_404_NOT_FOUND


@restx_api.errorhandler(InternalServerError)
def handle_internal_server_error(error):
    """Return JSON for HTTP 500 errors"""
    app.logger.error("500 Internal Server Error: %s", error)
    return {
        "error": "Internal Server Error",
        "message": str(error),
    }, status.HTTP_500_INTERNAL_SERVER_ERROR


@restx_api.errorhandler(Exception)
def handle_unexpected_exception(error):
    """Catch all unhandled exceptions as 500 JSON"""
    app.logger.exception("Unexpected server error: %s", error)
    return {
        "error": "Internal Server Error",
        "message": str(error),
    }, status.HTTP_500_INTERNAL_SERVER_ERROR
