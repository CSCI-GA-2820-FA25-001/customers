# Customers Service

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://python.org/)

This microservice manages customer accounts for an eCommerce platform. It provides a RESTful API for creating, reading, updating, deleting, and listing customer records.

## Overview

The Customers Service is a Flask-based REST API that allows you to perform CRUD operations on customer data. It uses PostgreSQL for data persistence and follows Test-Driven Development (TDD) practices with 95%+ test coverage.

## Features

- **Create** new customer records
- **Read** individual customer details
- **Update** existing customer information
- **Delete** customer records
- **List** all customers
- Service metadata endpoint for health checks

## Technology Stack

- **Python 3.11**
- **Flask** - Web framework
- **PostgreSQL** - Database
- **SQLAlchemy** - ORM
- **pytest** - Testing framework

## Getting Started

### Prerequisites

- Docker Desktop
- Visual Studio Code with Remote Containers extension

### Setup

1. Clone this repository
2. Open the folder in VS Code
3. When prompted, click "Reopen in Container" (or use Command Palette: "Remote-Containers: Reopen in Container")
4. Wait for the container to build and start

### Initialize the Database
`flask run`

The service will start on https://localhost:8000

### Running Tests
Run all tests with coverage report:
`make test`

### API Documentation
BASE URL: https://localhost:8000

### Endpoints
Get information and verify it's running: `GET /`

Response: `200 OK`

```json
{
  "name": "Customers Service",
  "version": "v1.0.0",
  "description": "Service managing customer accounts for the eCommerce site",
  "list_url": "/customers"
}
```

1. Create Customer
   
   Create a new customer record.
   
   Request:
   
    ```http
    POST /customers
    Content-Type: application/json
    
    {
        "first_name": "John",
        "last_name": "Doe",
        "address": "123 Main Street, New York, NY 10001"
    }
    ```
    
    Response: `201 Created`
    
    ```json
    {
        "id": 1,
        "fist_name": "John",
        "last_name": "Doe",
        "address": "123 Main Street, New York, NY 10001"
    }
    ```
    
    Error Responses:
    - `400 Bad Request` - Invalid or missing data
    - `500 Internal Server Error` - Server error

2. List All Customers
   
   Retrieve all customer records.
   
   Request:
   
   `GET /customers`
   
   `Response: 200 OK`

   ```json
   [
    {
        "id": 1,
        "first_name": "John"
        "last_name": "Doe"
        "address": "123 Main Street, New York, NY 10001"
    },
    
    {
        "id": 2,
        "first_name": "Jane"
        "last_name": "Smith"
        "address": "456 Oak Avenue, Brooklyn, NY 11201",
    }
    ]
    ```
    Error Responses: `500 Internal Server Error` - Server error


3. Read Customer
   
   Get a specific customer by ID.
   
   Request: `GET /customers/{id}`
   
   Response: `200 OK`

   ```json
   {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "address": "123 Main Street, New York, NY 10001"
    }
    ```
    Error Responses: `404 Not Found` - Customer does not exist


4. Update Customer
   
   Update an existing customer record.
   
   Request: `PUT /customers/{id}`
   
   Content-Type: `application/json`
   
   ```json
   {
    "first_name": "John",
    "last_name": "Doe",
    "address": "789 New Street, Queens, NY 11354"
   }
   ```
   Response: `200 OK`
   
   ```json
   {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "address": "789 New Street, Queens, NY 11354"
    }
    ```
    
    Error Responses:
    - `404 Not Found` - Customer does not exist
    - `400 Bad Request` - Invalid data


5. Delete Customer
   
   Delete a customer record.
   
   Request: `DELETE /customers/{id}`
   
   Response: `204 No Content`
   
   Error Responses: `404 Not Found` - Customer does not exist

### Testing

Unit Tests - Test business logic in models.py

Integration Tests - Test API endpoints in routes.py

### Development

#### Code Quality

The project uses:
- pylint for code linting
- black for code formatting (optional)
- pytest-cov for coverage reporting

Run linting:

`bashmake lint`

### Making Changes

1. Write tests first (TDD approach)
2. Implement the feature
3. Ensure all tests pass: make test
4. Verify coverage stays above 95%

### License
Copyright (c) 2016, 2025 John Rofrano. All rights reserved.

Licensed under the Apache License. See LICENSE
This repository is part of the New York University (NYU) masters class: CSCI-GA.2820-001 DevOps and Agile Methodologies created and taught by John Rofrano.
