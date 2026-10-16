"""Domain-neutral failures from exact geometry evaluation."""


class EvaluationError(ValueError):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def invalid(code, message):
    raise EvaluationError("INVALID", code, message)
