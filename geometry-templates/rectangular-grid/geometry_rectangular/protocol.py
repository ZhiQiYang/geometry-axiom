"""Decode this recipe's successful native result, without deriving grid lines.

This is a bounded second-template witness protocol, not the application's
scene language or a claim that native general source-graph coverage is complete.
"""
from dataclasses import dataclass
import re

from geometry_kernel import (DependencyEdge, EvaluationError, FrameDef,
    ProvenanceTemplate, Quantity, QuantityType, RegionDef, RegionSetDef,
    SourceContext, SourceDescriptor, SourceKey, SourceRef, Unit, ValueType,
    digest, strict_json_loads)

from . import GridCell, RectangularGridView


# Not frozen: Python writes __traceback__ on chained exceptions (unittest,
# contextlib).  eq=False keeps BaseException's identity __eq__/__hash__.
@dataclass(eq=False)
class RejectedView(ValueError):
    code: str
    message: str


def _fail(message):
    raise RejectedView("INVALID_VIEW", message)


def _shape(value, names):
    if type(value) is not dict or set(value) != set(names):
        _fail("Rectangular grid result has an invalid object shape")
    return value


def _integer(value, *, positive=False, unsigned=False):
    if type(value) is not str or re.fullmatch(r"-?(?:0|[1-9][0-9]*)", value) is None:
        _fail("Rectangular grid values must use exact decimal integer strings")
    try:
        result = int(value)
    except ValueError:
        _fail("Rectangular grid integer exceeds supported decoding limits")
    if str(result) != value or (positive and result <= 0) or (unsigned and not 0 <= result <= 0xFFFFFFFFFFFFFFFF):
        _fail("Rectangular grid integer is outside its declared domain")
    return result


def _key(value):
    _shape(value, ("owner", "field", "kind"))
    if value["kind"] not in ("length", "count"):
        _fail("Rectangular grid source kind is unknown")
    return SourceKey("rectangular-grid.inputs", (
        _integer(value["owner"], positive=True, unsigned=True),
        _integer(value["field"], positive=True, unsigned=True), value["kind"]))


def decode_view(payload, *, execution_identity=()):
    """Accept only complete native results and preserve exact source identity."""
    try:
        if type(execution_identity) is not tuple:
            _fail("Execution identity must be immutable")
        data = strict_json_loads(payload)
        if type(data) is not dict or data.get("schema") != "rectangular-grid-native-view/1":
            _fail("Rectangular grid result schema is unsupported")
        if data.get("status") != "OK":
            _shape(data, ("schema", "status", "previousUnchanged", "diagnostic"))
            if type(data["status"]) is not str or not data["status"] or data["previousUnchanged"] is not True:
                _fail("Rejected native result did not preserve its previous value")
            raise RejectedView(data["status"], "Native grid evaluation rejected this candidate")
        _shape(data, ("schema", "status", "recipe", "sources", "bindings", "frame", "cells"))
        if data["recipe"] != "rectangular-grid/1" or type(data["sources"]) is not list or len(data["sources"]) != 5:
            _fail("A complete rectangular grid result needs its five typed sources")
        context = SourceContext()
        sources, revisions = {}, {}
        for item in data["sources"]:
            _shape(item, ("key", "revision", "value"))
            key = _key(item["key"])
            revision = _integer(item["revision"], positive=True, unsigned=True)
            value = _shape(item["value"], ("num", "den", "unit"))
            dimension = key.key[-1] == "length"
            if value["unit"] != ("length" if dimension else "scalar"):
                _fail("Rectangular grid quantity unit and field kind disagree")
            quantity = Quantity(QuantityType.DIMENSION if dimension else QuantityType.COUNT,
                _integer(value["num"], positive=True), _integer(value["den"], positive=True),
                Unit.MM if dimension else Unit.UNITLESS)
            if quantity.denominator != 1:
                _fail("A successful rectangular grid result must have integral source values")
            source = SourceDescriptor(key, ValueType.QUANTITY, context, (), quantity,
                                      origin=(key.namespace, *key.key))
            if key in sources and (sources[key] != source or revisions[key] != revision):
                _fail("Aliased rectangular grid fields disagree about one source value")
            sources[key], revisions[key] = source, revision
        names = ("width", "height", "columns", "rows", "thickness")
        _shape(data["bindings"], names)
        bindings = {name: _key(data["bindings"][name]) for name in names}
        if set(bindings.values()) != set(sources):
            _fail("Every rectangular grid source must have one explicit binding")
        for name, key in bindings.items():
            if key.key[-1] != ("count" if name in ("columns", "rows") else "length"):
                _fail("Rectangular grid source binding has the wrong kind")
        columns, rows = (sources[bindings[name]].value.numerator for name in ("columns", "rows"))
        if columns > 32 or rows > 32 or columns * rows > 256:
            _fail("Rectangular grid result exceeds the native recipe's capacity")
        definition = tuple((name, key.namespace, key.key) for name, key in bindings.items())
        axes = _shape(data["frame"], ("origin", "u", "v", "n"))
        frame_key = SourceKey("rectangular-grid.result", ("frame", definition))
        frame = FrameDef(*(axes[name] for name in ("origin", "u", "v", "n")))
        frame_source = SourceDescriptor(frame_key, ValueType.FRAME, context, (), frame,
                                       origin=(frame_key.namespace, *frame_key.key))
        descriptors = [*sources.values(), frame_source]
        cells, identities = [], set()
        if type(data["cells"]) is not list or len(data["cells"]) != columns * rows:
            _fail("Rectangular grid result is missing native cells")
        dependencies = tuple(DependencyEdge(key) for key in dict.fromkeys(bindings[name] for name in names[:4]))
        for item in data["cells"]:
            _shape(item, ("column", "row", "region"))
            column, row = item["column"], item["row"]
            if type(column) is not int or type(row) is not int or not 0 <= column < columns or not 0 <= row < rows or (column,row) in identities:
                _fail("Native cell coordinates must be complete and unique")
            identities.add((column,row))
            region = _shape(item["region"], ("outer", "holes"))
            value = RegionSetDef((RegionDef(region["outer"], region["holes"]),))
            key = SourceKey("rectangular-grid.result", ("cell", definition, column, row))
            descriptors.append(SourceDescriptor(key, ValueType.REGION_SET, context, dependencies, value,
                                                origin=(key.namespace, *key.key)))
            provenance = ProvenanceTemplate((key.namespace, *key.key), (row,column))
            cells.append(GridCell(column, row, SourceRef(key, ValueType.REGION_SET, context), provenance))
        return RectangularGridView(tuple(descriptors), SourceRef(frame_key, ValueType.FRAME, context),
            SourceRef(bindings["thickness"], ValueType.QUANTITY, context),
            tuple(sorted(cells, key=lambda item: (item.row,item.column))),
            ("rectangular-grid/1", tuple(sorted((key.namespace,key.key,revision) for key,revision in revisions.items())),
             digest(data), execution_identity))
    except EvaluationError as error:
        raise RejectedView("INVALID_VIEW", "Invalid exact rectangular grid result: " + error.code) from error
