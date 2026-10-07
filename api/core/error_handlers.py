"""Gestionnaires d'erreurs : toutes les erreurs ont le même format JSON.

Format : {"error": {"code": "...", "message": "...", "details": [...]}}
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.core.exceptions import DataFlowError

logger = logging.getLogger(__name__)

_HTTP_ERROR_CODES = {
    400: "bad_request",
    404: "not_found",
    405: "method_not_allowed",
}


def build_error_body(
    code: str, message: str, details: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """Construit le corps JSON d'une erreur."""
    error: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return {"error": error}


async def handle_dataflow_error(_: Request, exc: Exception) -> JSONResponse:
    """Erreurs métier de l'application."""
    assert isinstance(exc, DataFlowError)
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_body(exc.error_code, exc.message),
    )


async def handle_validation_error(_: Request, exc: Exception) -> JSONResponse:
    """Requêtes invalides (validation Pydantic)."""
    assert isinstance(exc, RequestValidationError)
    details = [
        {
            # "body" est un préfixe interne à FastAPI/Pydantic, sans intérêt
            # pour le client : on ne garde que le chemin du champ concerné.
            "field": ".".join(
                str(part) for part in error["loc"] if part != "body"
            ),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=build_error_body(
            "validation_error", "La requête contient des données invalides.", details
        ),
    )


async def handle_http_error(_: Request, exc: Exception) -> JSONResponse:
    """Erreurs HTTP génériques (404 route inconnue, 405 méthode interdite...)."""
    assert isinstance(exc, StarletteHTTPException)
    code = _HTTP_ERROR_CODES.get(exc.status_code, "http_error")
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_body(code, str(exc.detail)),
    )


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Filet de sécurité : ne jamais exposer de détails internes au client."""
    logger.exception("Erreur non gérée sur %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content=build_error_body("internal_error", "Erreur interne du serveur."),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Branche tous les gestionnaires sur l'application."""
    app.add_exception_handler(DataFlowError, handle_dataflow_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
