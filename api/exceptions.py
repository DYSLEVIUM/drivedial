import logging
from typing import Optional

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("api")


class DriveDialError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "An unexpected error occurred."
    default_code = "error"


class TwilioError(DriveDialError):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "Twilio connection failed."
    default_code = "twilio_error"


class OpenAIError(DriveDialError):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "OpenAI service error."
    default_code = "openai_error"


def custom_exception_handler(exc: Exception, context: dict) -> Optional[Response]:
    response = exception_handler(exc, context)
    request = context.get("request")
    request_id = getattr(request, "request_id",
                         "unknown") if request else "unknown"

    if response is not None:
        response.data = {
            "error": {
                "code": getattr(exc, "default_code", "error"),
                "message": str(exc.detail) if hasattr(exc, "detail") else str(exc),
            },
            "request_id": request_id,
        }
        logger.warning(f"API error: {exc}")
    else:
        logger.exception(f"Unhandled exception: {exc}")
        response = Response(
            {"error": {"code": "internal_error",
                       "message": "An error occurred."}, "request_id": request_id},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
