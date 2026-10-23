"""Legacy ModelWorld behavior using the shared neutral candidate cell."""
from copy import deepcopy
import os
import sys

from geometry_kernel.transactions import CandidateCell, CandidateError

from .model_common import ModelError, digest
from .source_closure import binary_identity, current_identity


def runtime_stamp(*, base_executable, resolve_adapter, provider_identity):
    identity = current_identity()
    if not identity["fresh"]:
        raise ModelError("INVALID", "MODEL_RUNTIME_CHANGED", "I30", "Modeling runtime or provider changed since it was loaded")
    program = base_executable or os.environ.get("GEOMETRY_MODEL_BASE") or resolve_adapter()
    distro = (os.environ.get("GEOMETRY_MODEL_BASE_WSL_DISTRO")
              if sys.platform == "win32" and base_executable is None else None)
    try:
        binary = binary_identity(program, wsl_distro=distro)
    except (OSError, ValueError) as error:
        raise ModelError("UNSUPPORTED", "BASE_EXECUTABLE", "I32", "Cannot identify the C scene adapter bytes") from error
    return (provider_identity, identity["loaded"], binary)


class ModelWorld:
    def __init__(self, definitions, request, *, build, verify, stamp_reader, options):
        self._options = deepcopy(options)
        self._build = build
        self._verify = verify
        self._stamp_reader = stamp_reader
        package = build(definitions, request, **self._options)
        # Initial schema/source validation keeps its existing precedence over
        # adapter identity checks; candidate pinning starts after this succeeds.
        stamp_reader()
        self._cell = CandidateCell(package)

    def _same_stamp(self, expected):
        current = self._stamp_reader()
        if current != expected:
            raise ModelError("INVALID", "MODEL_RUNTIME_CHANGED", "I30", "Modeling runtime or provider changed during evaluation")
        return current

    @staticmethod
    def _candidate_error(error, *, cancel=False):
        if error.code == "EVALUATOR_CHANGED":
            return ModelError("INVALID", "MODEL_RUNTIME_CHANGED", "I30", "Modeling runtime or provider differs from the preview")
        message = "Preview token does not match" if cancel else "Preview is absent, cancelled, replaced or stale"
        return ModelError("INVALID", "STALE_PREVIEW", "I30", message)

    @property
    def package(self):
        return self._cell.value

    @property
    def definitions(self):
        return self._cell.value["definitions"]

    def export(self, request=None):
        current = self._cell.value
        stamp = self._stamp_reader()
        result = self._build(current["definitions"], current["request"] if request is None else request, **self._options)
        self._same_stamp(stamp)
        return result

    def preview(self, definitions, request=None):
        generation = self._cell.begin_preview()
        stamp = self._stamp_reader()
        current = self._cell.value
        candidate = self._build(definitions, current["request"] if request is None else request, **self._options)
        self._same_stamp(stamp)
        try:
            token = self._cell.seal_preview(generation, candidate, digest(candidate), stamp)
        except CandidateError as error:
            raise self._candidate_error(error) from error
        return {"token": token, "status": candidate["derived"]["status"],
                "diagnostics": deepcopy(candidate["diagnostics"]), "package": deepcopy(candidate)}

    def confirm(self, token):
        try:
            initial_stamp = self._stamp_reader()
        except ModelError:
            # A matching preview that encountered a changed/unavailable runtime
            # cannot revive if those bytes are restored later.
            try:
                self._cell.cancel(token)
            except CandidateError as error:
                raise self._candidate_error(error) from error
            raise
        try:
            receipt, pending = self._cell.claim(token, initial_stamp)
            stamp = self._stamp_reader()
            candidate = self._verify(pending, max_cells=self._options.get("max_cells", 200000),
                                     base_executable=self._options.get("base_executable"))
            self._same_stamp(stamp)
            return self._cell.commit(receipt, candidate, stamp)
        except CandidateError as error:
            raise self._candidate_error(error) from error

    commit = confirm

    def cancel(self, token=None):
        try:
            self._cell.cancel(token)
        except CandidateError as error:
            raise self._candidate_error(error, cancel=True) from error
