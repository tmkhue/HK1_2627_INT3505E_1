from http import HTTPStatus
from werkzeug.exceptions import HTTPException

from flask import current_app, g, jsonify


class ApiError(Exception):
    """Base class for expected API errors returned in Flask-Smorest's format."""

    status_code = HTTPStatus.BAD_REQUEST

    def __init__(self, message, *, errors=None):
        super().__init__(message)
        self.message = message
        self.errors = errors


class ProductNotFoundError(ApiError):
    status_code = HTTPStatus.NOT_FOUND

    def __init__(self, message="Product not found"):
        super().__init__(message)


class ProductOutOfStockError(ApiError):
    status_code = HTTPStatus.BAD_REQUEST

    def __init__(self, message="Product out of stock"):
        super().__init__(message)


def _error_response(status_code, message, errors=None):
    """Build the same top-level shape used by Flask-Smorest error responses."""
    payload = {
        "code": int(status_code),
        "status": HTTPStatus(status_code).phrase,
        "message": message,
    }
    if errors:
        payload["errors"] = errors
    return jsonify(payload), int(status_code)


def register_error_handlers(app):
    """Register handlers for application errors and unexpected exceptions."""
    @app.errorhandler(ApiError)
    def _on_api_error(error):
        return _error_response(error.status_code, error.message, error.errors)

    @app.errorhandler(HTTPException)
    def _on_http_error(error):
        return _error_response(error.code, error.description, None)

    @app.errorhandler(Exception)
    def _on_err(error):
        current_app.logger.exception(
            "Unhandled API exception",
            exc_info=error,
            extra={
                "event": "app.exception",
                "request_id": getattr(g, "request_id", None),
            },
        )
        return _error_response(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "Internal server error",
        )
