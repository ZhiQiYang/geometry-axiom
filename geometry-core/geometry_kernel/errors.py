"""Domain-neutral failures from exact geometry evaluation."""


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
        values = {name: getattr(self, name) for name in
                  ("node", "path", "missing", "root", "diagnostics", "phase")}
        values.update(context)
        return EvaluationError(self.status, self.code, self.message, **values)


def raise_errors(errors):
    if not errors:
        return
    priority = {"INVALID": 3, "UNSUPPORTED": 2, "INCOMPLETE": 1}
    strongest = max(errors, key=lambda item: priority[item.status])
    diagnostics = tuple(item for error in errors for item in (error.diagnostics or (error,)))
    raise strongest.contextualized(diagnostics=diagnostics)


def invalid(code, message):
    raise EvaluationError("INVALID", code, message)
