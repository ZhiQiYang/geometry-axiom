"""A real typed-program consumer of the shared atomic candidate cell."""
from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum

from .canonical import digest
from .evaluate import evaluate
from .graph import Limits
from .transactions import CandidateCell


def _plain(value):
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if type(value) is dict:
        return {key: _plain(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [_plain(item) for item in value]
    return value


@dataclass(frozen=True)
class ProgramSnapshot:
    program: object
    request: object
    result: object


class ProgramSession:
    """Preview and confirm source-graph replacements without template state.

    The caller supplies an opaque evaluator identity for each operation. This
    pure layer compares it; only a host can know how to read current providers.
    """

    def __init__(self, program, request, *, limits=Limits()):
        self._limits = limits
        self._cell = CandidateCell(ProgramSnapshot(program, request, evaluate(program, request, limits=limits)))

    @property
    def snapshot(self):
        return self._cell.value

    @property
    def revision(self):
        return self._cell.revision

    def preview(self, program, request=None, *, evaluator_stamp):
        generation = self._cell.begin_preview()
        selected_request = self._cell.value.request if request is None else request
        result = evaluate(program, selected_request, limits=self._limits)
        candidate = ProgramSnapshot(program, selected_request, result)
        content = digest(_plain((program, selected_request, self._limits)))
        token = self._cell.seal_preview(generation, candidate, content, evaluator_stamp)
        return token, candidate

    def confirm(self, token, *, evaluator_stamp):
        receipt, candidate = self._cell.claim(token, evaluator_stamp)
        verified = ProgramSnapshot(candidate.program, candidate.request,
                                   evaluate(candidate.program, candidate.request, limits=self._limits))
        return self._cell.commit(receipt, verified, evaluator_stamp)

    def cancel(self, token=None):
        self._cell.cancel(token)
