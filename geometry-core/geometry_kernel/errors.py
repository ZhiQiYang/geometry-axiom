"""Domain-neutral failures from exact geometry evaluation."""
from copy import deepcopy


class EvaluationError(ValueError):
    def __init__(self, status, code, message, *, node=None, path=(), missing=None,
                 root=None, diagnostics=(), phase="evaluation"):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.node = node
        self.path = tuple(path)
        self.missing = missing
        self.root = root
        self.diagnostics = tuple(diagnostics)
        self.phase = phase

    def contextualized(self, **context):
        values = {"node": self.node, "path": self.path, "missing": self.missing,
                  "root": self.root, "diagnostics": self.diagnostics, "phase": self.phase}
        values.update(context)
        return EvaluationError(self.status, self.code, self.message, **values)

    def __deepcopy__(self, memo):
        return EvaluationError(self.status, self.code, self.message,
            node=deepcopy(self.node, memo), path=deepcopy(self.path, memo),
            missing=deepcopy(self.missing, memo), root=deepcopy(self.root, memo),
            diagnostics=deepcopy(self.diagnostics, memo), phase=self.phase)


def raise_errors(errors):
    if not errors:
        return
    priority = {"INVALID": 3, "UNSUPPORTED": 2, "INCOMPLETE": 1}
    strongest = max(errors, key=lambda item: priority[item.status])
    diagnostics = tuple(item for error in errors for item in (error.diagnostics or (error,)))
    raise strongest.contextualized(diagnostics=diagnostics)


def invalid(code, message):
    raise EvaluationError("INVALID", code, message)
