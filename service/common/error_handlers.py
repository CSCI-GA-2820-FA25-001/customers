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
Module: error_handlers
"""
from flask import jsonify

######################################################################
# Error Handlers
######################################################################


def register_error_handlers(app):
    """Register error handlers"""

    @app.errorhandler(400)
    def bad_request(error):
        """Bad Request"""
        return jsonify({
            "error": "Bad Request",
            "message": str(error.description or "Invalid request")
        }), 400

    @app.errorhandler(401)  # Note: TWO blank lines above this line
    def unauthorized(error):
        """Unauthorized"""
        return jsonify({
            "error": "Unauthorized",
            "message": "Authentication required"
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        """Forbidden"""
        return jsonify({
            "error": "Forbidden",
            "message": "Access denied"
        }), 403

    @app.errorhandler(404)  # Note: TWO blank lines above this line
    def not_found(error):
        """Not Found"""
        # Handle Flask-RESTX validation errors for non-integer IDs
        error_msg = str(error.description or "")
        if "The requested URL" in error_msg or "did you mean" in error_msg:
            # This is likely a non-integer ID validation error
            return jsonify({
                "error": "Bad Request",
                "message": "Customer id must be an integer"
            }), 400
        return jsonify({
            "error": "Not Found",
            "message": "Resource not found"
        }), 404

    @app.errorhandler(405)  # Note: TWO blank lines above this line
    def method_not_allowed(error):
        """Method Not Allowed"""
        return jsonify({
            "error": "Method Not Allowed",
            "message": str(error.description or "Method not allowed")
        }), 405

    @app.errorhandler(415)  # Note: TWO blank lines above this line
    def unsupported_media_type(error):
        """Unsupported Media Type"""
        return jsonify({
            "error": "Unsupported Media Type",
            "message": "Content-Type must be application/json"
        }), 415

    @app.errorhandler(500)  # Note: TWO blank lines above this line
    def internal_error(error):
        """Internal Server Error"""
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }), 500
