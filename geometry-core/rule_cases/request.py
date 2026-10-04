"""A data-only backend seam for the shared serve owner; no registered route.

The request body is one complete rule-case/1 definition. Project scope,
generation, executable path and cancellation come from the host adapter, never
from extra case fields. Persistence and contextToken/history remain host-owned.
"""
from .definition import decode_case
from .executor import MAX_OUTPUT_BYTES, NativeExecutor


def run_case_request(body, *, project_id, generation, binary=None, cancel=None,
                     timeout_seconds=5, max_output_bytes=MAX_OUTPUT_BYTES):
    """Validate bounded UTF-8 JSON before creating a fresh native executor.

CaseDefinitionError describes a pre-execution definition error. A valid request
returns the executor's plain JSON receipt, including every nonpass status. The
caller must check its captured contextToken before saving that receipt.
"""
    definition = decode_case(body)
    executor = NativeExecutor(binary, timeout_seconds=timeout_seconds,
                              max_output_bytes=max_output_bytes)
    return executor.run(definition, project_id=project_id, generation=generation, cancel=cancel)
