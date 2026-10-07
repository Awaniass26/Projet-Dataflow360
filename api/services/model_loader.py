"""Chargement générique d'un modèle sérialisé (joblib ou pickle)."""

import pickle
from functools import lru_cache
from pathlib import Path
from typing import Any

from api.core.exceptions import ModelLoadError, ModelNotConfiguredError
from api.services.ml_contracts import ModelArtifactFormat


def _load_joblib(path: Path) -> Any:
    import joblib  # import local : évite la dépendance si jamais inutilisée

    return joblib.load(path)


def _load_pickle(path: Path) -> Any:
    with path.open("rb") as file_obj:
        return pickle.load(file_obj)  # noqa: S301 - fichier interne au projet


_LOADERS = {
    ModelArtifactFormat.JOBLIB: _load_joblib,
    ModelArtifactFormat.PICKLE: _load_pickle,
}


@lru_cache(maxsize=8)
def load_model(path_str: str, artifact_format: ModelArtifactFormat) -> Any:
    """Charge un modèle depuis le disque, avec mise en cache.

    Raises:
        ModelNotConfiguredError: si `path_str` est vide/None.
        ModelLoadError: si le fichier est introuvable ou illisible.
    """
    if not path_str:
        raise ModelNotConfiguredError()

    path = Path(path_str)
    if not path.is_file():
        raise ModelLoadError(f"Fichier modèle introuvable : {path}")

    try:
        return _LOADERS[artifact_format](path)
    except ModelNotConfiguredError:
        raise
    except Exception as exc:  # noqa: BLE001 - on veut convertir toute erreur
        raise ModelLoadError(f"Échec du chargement du modèle ({path}) : {exc}") from exc
