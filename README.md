# Guidance for Task: Order Processing API (FastAPI)

## Task Overview
You are provided with a starter codebase for an order management API designed for e-commerce scenarios. The API is implemented with FastAPI, Pydantic, and SQLAlchemy. Your task is to refine, complete, and ensure the solution meets the following requirements.

## Requirements
- **Endpoints**:
  - Create a new order (restricted to staff).
  - Update order status (restricted to staff), which must trigger a background task simulating an email notification to the customer.
  - Get order details (open to all).
- **RBAC**: Implement a role check where 'staff' role is required for order creation and updates. Roles are controlled via the `X-User-Role` header (e.g., `staff`, `customer`).
- **Data Validation**: Use Pydantic models to validate all request bodies strictly.
- **Persistence**: Persist orders using SQLAlchemy ORM with SQLite as storage.
- **Background Processing**: On order status update, use FastAPI's BackgroundTask to trigger a function that "sends" a notification (simulate sending email; for this task, logging suffices).
- **Logging**: All order creation, updates, and notifications should be logged in a structured (machine-parseable) format suitable for post-processing, like JSON-style logs.
- **Error Responses**: Meaningful error messages (e.g., 403 for unauthorized actions, 404 for not found, 422 for invalid input).
- **API Routing**: Use FastAPI routers to organize the endpoints cleanly.
- **OpenAPI Docs**: The application should expose full auto-generated and interactive documentation via FastAPI's OpenAPI.
- **Code Quality**: The code should be clean, maintainable, adequately structured, and production-ready in style (though not feature-complete for a real deployment).

## Verifying Your Solution
- Ensure only users with the `X-User-Role: staff` header can create or update orders. Attempts from others should yield a 403 error.
- New orders must be stored in the database with correct details.
- Order updates must log an order update and trigger a background task that logs a simulated notification to the customer in structured format.
- Error scenarios (such as updating non-existent orders, invalid payloads, or attempts by unauthorized users) should be handled gracefully with appropriate status codes and messages.
- API docs should fully reflect request/response schemas and available endpoints.
- Output logs must be parseable, e.g., key/value or JSON-style entries for easy downstream processing.
- The codebase must be understandable and maintainable, leveraging FastAPI idioms.

If you meet all the above with clean, well-structured code, your solution should be complete for this assessment.
