"""Compatibility entry point for the explicitly assembled host/K/W runtime."""
from . import _host
from geometry_app.bootstrap import default_provider
from geometry_app.model_runtime import ModelingRuntime
from geometry_app.model_geometry import prefix as _prefix

# Keep the public executor capability tuple while the policy lives in W.
CAPABILITIES = default_provider().capabilities


def evaluate(definitions, request, *, capabilities=None, max_cells=200000,
             base_executable=None):
    from .base import load_base
    runtime = ModelingRuntime(provider=default_provider(), native_loader=load_base)
    return runtime.evaluate(definitions, request, capabilities=capabilities,
                            max_cells=max_cells, base_executable=base_executable)
