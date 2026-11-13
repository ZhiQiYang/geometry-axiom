"""The host owns repository package discovery; K and templates never do it."""
from pathlib import Path
import sys


def configure_packages():
    repository = Path(__file__).resolve().parents[2]
    for relative in ("geometry-core", "geometry-templates/woodworking"):
        path = str(repository / relative)
        if path not in sys.path:
            sys.path.insert(0, path)


def default_provider():
    configure_packages()
    from .model_common import ModelError
    try:
        from geometry_woodworking.model_policy import WoodworkingModelProvider
    except ImportError as error:
        raise ModelError("UNSUPPORTED", "MODEL_PROVIDER", "I32", "The configured modeling provider is unavailable") from error
    return WoodworkingModelProvider()
