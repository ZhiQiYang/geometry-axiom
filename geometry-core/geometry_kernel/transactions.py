"""Copied candidate state with a single-use preview/confirmation boundary.

The caller evaluates the candidate and validates the claimed copy. This module
does not choose an evaluator, inspect its sources, or assign object identities.
Its evaluator stamp is an opaque immutable value supplied by that caller.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import secrets
from threading import RLock
from typing import Generic, TypeVar


T = TypeVar("T")


class CandidateError(ValueError):
    """A stale candidate or changed evaluator cannot replace committed state."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.status = "INVALID"
        self.code = code
        self.message = message


def _stale():
    return CandidateError("STALE_PREVIEW", "Preview is absent, cancelled, replaced or stale")


def _changed():
    return CandidateError("EVALUATOR_CHANGED", "Evaluator stamp differs from the preview")


def _check_stamp(stamp: tuple) -> None:
    def immutable(value):
        return (value is None or type(value) in (str, int)
                or type(value) is tuple and all(immutable(item) for item in value))

    if type(stamp) is not tuple or not immutable(stamp):
        raise TypeError("Evaluator stamp must be a tuple of tuples, strings, integers or None")


def _token_value(value):
    """Preserve opaque types without decimal integer conversion limits."""
    if value is None:
        return ("none",)
    if type(value) is int:
        return ("int", hex(value))
    if type(value) is str:
        return ("str", value)
    return ("tuple", tuple(_token_value(item) for item in value))


@dataclass(frozen=True)
class _Pending(Generic[T]):
    token: str
    revision: int
    generation: int
    evaluator_stamp: tuple
    value: T


@dataclass(frozen=True)
class _Claim:
    receipt: object
    revision: int
    generation: int
    evaluator_stamp: tuple


class CandidateCell(Generic[T]):
    """Own committed state; issue tokens and private, one-use claim receipts.

    ``begin_preview`` must precede external evaluation, even if that evaluation
    fails. ``claim`` consumes the matching preview before external verification.
    The caller then re-reads its runtime stamp and passes the verified value to
    ``commit``. Verification failures require no rollback: committed state has
    not changed. Calling ``cancel()`` also invalidates work already claimed.
    """

    def __init__(self, initial_value: T):
        self._value = deepcopy(initial_value)
        self._revision = 0
        self._generation = 0
        self._nonce = secrets.token_hex(32)
        self._pending: _Pending[T] | None = None
        self._claimed: _Claim | None = None
        self._open_generation: int | None = None
        self._lock = RLock()

    def __copy__(self):
        raise TypeError("CandidateCell owners cannot be copied; create a new cell from .value")

    def __deepcopy__(self, memo):
        raise TypeError("CandidateCell owners cannot be copied; create a new cell from .value")

    @property
    def value(self) -> T:
        with self._lock:
            value = self._value
        return deepcopy(value)

    @property
    def revision(self) -> int:
        with self._lock:
            return self._revision

    @property
    def generation(self) -> int:
        with self._lock:
            return self._generation

    def begin_preview(self) -> int:
        with self._lock:
            self._pending = None
            self._claimed = None
            self._generation += 1
            self._open_generation = self._generation
            return self._generation

    def seal_preview(self, generation: int, candidate_value: T,
                     content_digest: str, evaluator_stamp: tuple) -> str:
        with self._lock:
            if (type(generation) is not int or generation != self._generation
                    or generation != self._open_generation):
                raise _stale()
            self._open_generation = None
            revision = self._revision
        if type(content_digest) is not str:
            raise TypeError("Candidate content digest must be a string")
        _check_stamp(evaluator_stamp)
        value = deepcopy(candidate_value)
        identity = (self._nonce, revision, generation, content_digest, evaluator_stamp)
        token = hashlib.sha256(json.dumps(_token_value(identity), ensure_ascii=True,
                                         separators=(",", ":")).encode("ascii")).hexdigest()
        with self._lock:
            if revision != self._revision or generation != self._generation:
                raise _stale()
            self._pending = _Pending(token, revision, generation, evaluator_stamp, value)
        return token

    def claim(self, token: str, evaluator_stamp: tuple) -> tuple[object, T]:
        with self._lock:
            pending = self._pending
            if (pending is None or type(token) is not str or pending.token != token
                    or pending.revision != self._revision
                    or pending.generation != self._generation):
                raise _stale()
            self._pending = None
        try:
            _check_stamp(evaluator_stamp)
        except TypeError as exc:
            raise _changed() from exc
        if evaluator_stamp != pending.evaluator_stamp:
            raise _changed()
        value = deepcopy(pending.value)
        receipt = object()
        with self._lock:
            if pending.revision != self._revision or pending.generation != self._generation:
                raise _stale()
            self._claimed = _Claim(receipt, pending.revision, pending.generation,
                                   pending.evaluator_stamp)
        return receipt, value

    def commit(self, receipt: object, validated_value: T, evaluator_stamp: tuple) -> T:
        with self._lock:
            claimed = self._claimed
            if claimed is None or claimed.receipt is not receipt:
                raise _stale()
            self._claimed = None
            if claimed.revision != self._revision or claimed.generation != self._generation:
                raise _stale()
        try:
            _check_stamp(evaluator_stamp)
        except TypeError as exc:
            raise _changed() from exc
        if evaluator_stamp != claimed.evaluator_stamp:
            raise _changed()
        # Prepare both copies before swapping. Even a failed return-value copy
        # must leave the previous committed state intact and consume the receipt.
        value = deepcopy(validated_value)
        result = deepcopy(value)
        with self._lock:
            if claimed.revision != self._revision or claimed.generation != self._generation:
                raise _stale()
            self._value = value
            self._revision += 1
        return result

    def cancel(self, token: str | None = None) -> None:
        with self._lock:
            if token is not None and (self._pending is None or type(token) is not str
                                      or token != self._pending.token):
                raise _stale()
            self._pending = None
            self._claimed = None
            self._open_generation = None
            self._generation += 1
