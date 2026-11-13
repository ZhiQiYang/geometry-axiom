"""Compatibility import bootstrap for the explicitly assembled host package."""
from importlib.util import find_spec
from pathlib import Path
import sys

if find_spec("geometry_app") is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "geometry-app"))
from geometry_app.bootstrap import configure_packages
configure_packages()
from geometry_app.source_closure import initialize
initialize(Path(__file__).resolve().parent)
