"""Exceptions de l'API.

Chaque exception porte un code HTTP et un code d'erreur stable, que le
frontend peut utiliser sans dépendre du texte du message.
"""


class DataFlowError(Exception):
    """Erreur de base : toute sous-classe est renvoyée en JSON propre."""

    status_code: int = 500
    error_code: str = "internal_error"
    default_message: str = "Erreur interne du serveur."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class ResourceNotFoundError(DataFlowError):
    status_code = 404
    error_code = "resource_not_found"
    default_message = "Ressource introuvable."


class ModelNotConfiguredError(DataFlowError):
    status_code = 503
    error_code = "model_not_configured"
    default_message = "Le modèle ML n'est pas encore configuré."


class ModelLoadError(DataFlowError):
    status_code = 503
    error_code = "model_load_error"
    default_message = "Le modèle ML n'a pas pu être chargé."


class ModelPredictionError(DataFlowError):
    status_code = 500
    error_code = "model_prediction_error"
    default_message = "Le modèle ML n'a pas pu produire de résultat."


class DatabaseNotConfiguredError(DataFlowError):
    status_code = 503
    error_code = "database_not_configured"
    default_message = "PostgreSQL n'est pas configuré (variable DATABASE_URL absente)."


class DatabaseError(DataFlowError):
    status_code = 503
    error_code = "database_error"
    default_message = "La base de données est indisponible ou a renvoyé une erreur."


