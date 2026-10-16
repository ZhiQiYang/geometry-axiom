"""Historical import seam for the native process owner in geometry_app."""
from . import _host
from geometry_app import model_native as _native
from geometry_app.model_native import (
    _adapter_command, _build_adapter, startup_base_transport, subprocess, sys,
)


def load_base(scene_text: str, executable=None) -> dict:
    # Keep explicit historical patch points; process and protocol code live in H.
    return _native.load_base(scene_text, executable, builder=_build_adapter,
                             command_builder=_adapter_command)
