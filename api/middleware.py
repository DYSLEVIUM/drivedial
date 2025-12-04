import json
import logging
import time
import uuid
from typing import Callable

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("api")

SKIP_PATHS = {"/favicon.ico", "/static/", "/admin/jsi18n/"}


class RequestLoggingMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if any(request.path.startswith(p) for p in SKIP_PATHS):
            return self.get_response(request)

        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        self._log_request(request, request_id)
        response = self.get_response(request)
        duration = (time.perf_counter() - start) * 1000

        self._log_response(request, response, request_id, duration)
        response["X-Request-ID"] = request_id
        return response

    def _log_request(self, request: HttpRequest, request_id: str) -> None:
        client_ip = request.META.get(
            "HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
        client_ip = client_ip or request.META.get("REMOTE_ADDR", "unknown")

        logger.info(
            f"[{request_id}] {request.method} {request.path} from {client_ip}")

    def _log_response(
        self, request: HttpRequest, response: HttpResponse, request_id: str, duration: float
    ) -> None:
        level = logging.ERROR if response.status_code >= 500 else (
            logging.WARNING if response.status_code >= 400 else logging.INFO
        )
        logger.log(
            level, f"[{request_id}] {response.status_code} in {duration:.2f}ms")
