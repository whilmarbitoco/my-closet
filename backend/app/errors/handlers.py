class APIError(Exception):
    status_code = 400
    message = "A server error occurred."

    def __init__(self, message=None, status_code=None):
        self.message = message or self.message
        super().__init__(self.message)
        if status_code is not None:
            self.status_code = status_code

    def to_json(self):
        return {"error": self.message, "status_code": self.status_code}


# --- 4xx Client Errors ---

class ValidationError(APIError):
    status_code = 400
    message = "The request body contains invalid data."


class UnauthorizedError(APIError):
    status_code = 401
    message = "Authentication is required to access this resource."


class ForbiddenError(APIError):
    status_code = 403
    message = "You do not have permission to perform this action."


class NotFoundError(APIError):
    status_code = 404
    message = "The requested resource was not found."


class ConflictError(APIError):
    status_code = 409
    message = "A resource with this identifier already exists."


# --- 5xx Server Errors ---

class InternalServerError(APIError):
    status_code = 500
    message = "An unexpected error occurred on our end."
