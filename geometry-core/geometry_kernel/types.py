"""Immutable, validated inputs to the exact orthogonal geometry kernel.

Identity and ordering tokens are opaque. They never select an algorithm.
"""
from dataclasses import dataclass, replace
from enum import Enum
from fractions import Fraction

from .errors import invalid

COORDINATE_LIMIT = 100_000_000


def coordinate(value):
    if type(value) is not int or not -COORDINATE_LIMIT <= value <= COORDINATE_LIMIT:
        invalid("COORD_RANGE", "Coordinates must be exact integers in the supported range")
    return value


def vector(value, length=3):
    if not isinstance(value, (tuple, list)) or len(value) != length:
        invalid("VECTOR", "A coordinate vector has the wrong dimension")
    return tuple(coordinate(v) for v in value)


def exact_point(value, length):
    if not isinstance(value, (tuple, list)) or len(value) != length or any(type(v) not in (int, Fraction) for v in value):
        invalid("POINT_TYPE", "Geometric queries require exact integer or rational coordinates")
    return tuple(value)


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def area2(ring):
    return sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(ring, ring[1:]+ring[:1]))


def ring_location(point, ring):
    """0 outside, 1 boundary, 2 inside, with exact rational ray crossings."""
    x, y = point
    inside = False
    for a, b in zip(ring, ring[1:]+ring[:1]):
        side = (x-a[0])*(b[1]-a[1])-(y-a[1])*(b[0]-a[0])
        if side == 0 and min(a[0], b[0]) <= x <= max(a[0], b[0]) and min(a[1], b[1]) <= y <= max(a[1], b[1]):
            return 1
        if (a[1] > y) != (b[1] > y):
            intersect = a[0] + Fraction(b[0]-a[0], b[1]-a[1])*(y-a[1])
            if x < intersect:
                inside = not inside
    return 2 if inside else 0


def _intersects(a, b, c, d):
    # For orthogonal segments overlapping closed coordinate intervals are
    # necessary and sufficient, including endpoint and collinear contact.
    return all(max(min(a[i], b[i]), min(c[i], d[i])) <= min(max(a[i], b[i]), max(c[i], d[i])) for i in (0, 1))


def _ring(points):
    if not isinstance(points, (tuple, list)):
        invalid("REGION_LOOP", "A region loop must be a sequence")
    ring = tuple(vector(p, 2) for p in points)
    if len(ring) < 4 or len(set(ring)) != len(ring) or not area2(ring):
        invalid("REGION_LOOP", "A region loop needs distinct vertices and positive area")
    edges = tuple(zip(ring, ring[1:]+ring[:1]))
    for a, b in edges:
        if (a[0] == b[0]) == (a[1] == b[1]):
            invalid("REGION_EDGE", "Region edges must be nonzero and axis-aligned")
    for i, (a, b) in enumerate(edges):
        for j, (c, d) in enumerate(edges[i+1:], i+1):
            if j == i+1 or (i == 0 and j == len(edges)-1):
                # Consecutive collinear edges may continue, never backtrack.
                shared = b if j == i+1 else a
                other_a = a if j == i+1 else b
                other_b = d if j == i+1 else c
                if sum((other_a[k]-shared[k])*(other_b[k]-shared[k]) for k in (0, 1)) > 0:
                    invalid("REGION_SELF_INTERSECTION", "Adjacent region edges overlap")
            elif _intersects(a, b, c, d):
                invalid("REGION_SELF_INTERSECTION", "A region loop cannot cross or touch itself")
    return ring


def _rings_touch(first, second):
    return any(_intersects(a, b, c, d) for a, b in zip(first, first[1:]+first[:1]) for c, d in zip(second, second[1:]+second[:1]))


@dataclass(frozen=True)
class CoordinateDomain:
    key: tuple = ("world",)

    def __post_init__(self):
        if type(self.key) is not tuple:
            invalid("IDENTITY", "A coordinate domain needs an immutable identity tuple")
        _identity(self.key)


def _identity(value):
    if type(value) is tuple:
        for item in value:
            _identity(item)
    elif value is not None and type(value) not in (str, int):
        invalid("IDENTITY", "Identity tokens must be immutable strings, integers or tuples")


@dataclass(frozen=True)
class SourceKey:
    namespace: str
    key: tuple

    def __post_init__(self):
        if type(self.namespace) is not str or not self.namespace or type(self.key) is not tuple:
            invalid("SOURCE_KEY", "A source key needs a namespace and full immutable identity")
        _identity(self.key)


@dataclass(frozen=True)
class DefinitionValue:
    """Opaque provider definition; K retains its schema and exact content bytes.

    The provider owns the content's canonical encoding and domain validation.
    Empty content and whitespace-only schema names are valid neutral values.
    """
    schema: str
    content: bytes

    def __post_init__(self):
        if type(self.schema) is not str or not self.schema or "\0" in self.schema:
            invalid("DEFINITION_SCHEMA", "A definition requires a nonempty schema without NUL bytes")
        try:
            self.schema.encode("utf-8")
        except UnicodeEncodeError:
            invalid("DEFINITION_SCHEMA", "A definition schema requires valid Unicode")
        if type(self.content) is not bytes:
            invalid("DEFINITION_CONTENT", "Definition content must be immutable bytes")


class QuantityType(Enum):
    DIMENSION = "dimension"
    COUNT = "count"
    RATIO = "ratio"
    AXIS_POSITION = "axis-position"


class Unit(Enum):
    MM = "mm"
    UNITLESS = "unitless"


@dataclass(frozen=True)
class Quantity:
    value_type: QuantityType
    numerator: int
    denominator: int
    unit: Unit

    def __post_init__(self):
        if not isinstance(self.value_type, QuantityType) or not isinstance(self.unit, Unit):
            invalid("QUANTITY_TYPE", "An exact quantity needs a declared type and unit")
        if type(self.numerator) is not int or type(self.denominator) is not int or self.denominator <= 0:
            invalid("QUANTITY_VALUE", "An exact quantity needs an integer numerator and positive denominator")
        expected = Unit.MM if self.value_type in (QuantityType.DIMENSION, QuantityType.AXIS_POSITION) else Unit.UNITLESS
        if self.unit != expected:
            invalid("QUANTITY_UNIT", "Quantity type and unit disagree")
        value = Fraction(self.numerator, self.denominator)
        if self.value_type == QuantityType.COUNT and (value.denominator != 1 or value < 0):
            invalid("QUANTITY_VALUE", "A count must be a nonnegative exact integer")
        object.__setattr__(self, "numerator", value.numerator)
        object.__setattr__(self, "denominator", value.denominator)

    @property
    def value(self):
        return Fraction(self.numerator, self.denominator)


@dataclass(frozen=True)
class FrameDef:
    origin: tuple
    u: tuple
    v: tuple
    n: tuple
    domain: CoordinateDomain = CoordinateDomain()

    def __post_init__(self):
        object.__setattr__(self, "origin", vector(self.origin))
        object.__setattr__(self, "u", vector(self.u))
        object.__setattr__(self, "v", vector(self.v))
        object.__setattr__(self, "n", vector(self.n))
        if not isinstance(self.domain, CoordinateDomain) or any(sum(x*x for x in axis) != 1 for axis in (self.u, self.v, self.n)) or cross(self.u, self.v) != self.n:
            invalid("FACE_FRAME", "Frame requires right-handed orthogonal unit integer axes")

    def world(self, uv, height=0):
        uv = exact_point(uv, 2)
        exact_point((height,), 1)
        return tuple(self.origin[i]+uv[0]*self.u[i]+uv[1]*self.v[i]+height*self.n[i] for i in range(3))


@dataclass(frozen=True)
class RegionDef:
    outer: tuple
    holes: tuple = ()
    vertex_keys: tuple = ()

    def __post_init__(self):
        outer = _ring(self.outer)
        if not isinstance(self.holes, (tuple, list)) or type(self.vertex_keys) is not tuple:
            invalid("REGION_LOOP", "Region holes and vertex identities must be sequences")
        holes = tuple(_ring(hole) for hole in self.holes)
        for i, hole in enumerate(holes):
            if _rings_touch(outer, hole) or ring_location(hole[0], outer) != 2:
                invalid("REGION_HOLE", "A hole must lie strictly inside its outer loop")
            for previous in holes[:i]:
                if _rings_touch(previous, hole) or ring_location(hole[0], previous) or ring_location(previous[0], hole):
                    invalid("REGION_HOLE_OVERLAP", "Region holes cannot overlap, nest or touch")
        _identity(self.vertex_keys)
        if self.vertex_keys and len(self.vertex_keys) != sum(map(len, (outer,)+holes)):
            invalid("REGION_VERTEX_KEYS", "Each region vertex must have one stable key")
        if self.vertex_keys and len(set(self.vertex_keys)) != len(self.vertex_keys):
            invalid("REGION_VERTEX_KEYS", "Region vertex identities must be distinct")
        object.__setattr__(self, "outer", outer)
        object.__setattr__(self, "holes", holes)

    def location(self, point):
        point = exact_point(point, 2)
        outer = ring_location(point, self.outer)
        if outer != 2:
            return outer
        for hole in self.holes:
            location = ring_location(point, hole)
            if location:
                return 1 if location == 1 else 0
        return 2


@dataclass(frozen=True)
class RegionSetDef:
    components: tuple

    def __post_init__(self):
        if not isinstance(self.components, (tuple, list)):
            invalid("REGION_SET", "A region set must be a sequence of regions")
        object.__setattr__(self, "components", tuple(self.components))
        if any(not isinstance(item, RegionDef) for item in self.components):
            invalid("REGION_SET", "A region set contains only validated regions")
        # Inspect the exact planar arrangement, including every hole vertex.
        # Boundary contact is allowed; positive-area component overlap is not.
        for i, first in enumerate(self.components):
            for second in self.components[:i]:
                coords = [sorted({p[axis] for r in (first, second) for loop in (r.outer, *r.holes) for p in loop}) for axis in (0, 1)]
                for x0, x1 in zip(coords[0], coords[0][1:]):
                    for y0, y1 in zip(coords[1], coords[1][1:]):
                        point = (Fraction(x0+x1, 2), Fraction(y0+y1, 2))
                        if first.location(point) == second.location(point) == 2:
                            invalid("REGION_COMPONENT_OVERLAP", "Region components cannot have overlapping interiors")


@dataclass(frozen=True)
class Provenance:
    origin_handle: tuple
    feature_key: tuple
    order_token: tuple
    operation_path: tuple = ()
    contribution: str = "boundary"
    normal_sign: int = 1

    def __post_init__(self):
        for value in (self.origin_handle, self.feature_key, self.order_token, self.operation_path):
            if type(value) is not tuple:
                invalid("PROVENANCE", "Source identities and ordering tokens must be immutable tuples")
            _identity(value)
        if type(self.contribution) is not str or type(self.normal_sign) is not int or self.normal_sign not in (-1, 1):
            invalid("PROVENANCE", "Invalid source orientation or contribution")

    @property
    def sort_key(self):
        def ordered(value):
            if value is None:
                return (0,)
            if type(value) is int:
                return (1, value)
            if type(value) is str:
                return (2, value)
            return (3, tuple(ordered(item) for item in value))
        return ordered((*self.order_token, self.operation_path, self.contribution))

    def prefixed(self, path=(), *, contribution=None):
        return replace(self, operation_path=(*path, *self.operation_path), contribution=self.contribution if contribution is None else contribution)


@dataclass(frozen=True)
class BoxDef:
    frame: FrameDef
    lower: tuple
    upper: tuple
    face_origins: tuple

    def __post_init__(self):
        if not isinstance(self.frame, FrameDef):
            invalid("FACE_FRAME", "A box requires a validated frame")
        object.__setattr__(self, "lower", vector(self.lower))
        object.__setattr__(self, "upper", vector(self.upper))
        object.__setattr__(self, "face_origins", tuple(self.face_origins))
        if any(lo >= hi or hi-lo > COORDINATE_LIMIT for lo, hi in zip(self.lower, self.upper)):
            invalid("BOX_EXTENTS", "Box extents must have positive supported dimensions")
        if len(self.face_origins) != 6 or any(not isinstance(s, Provenance) for s in self.face_origins):
            invalid("BOX_SOURCES", "A box requires exactly six oriented face origins")
        from itertools import product
        for xyz in product(*zip(self.lower, self.upper)):
            vector(self.frame.world(xyz[:2], xyz[2]))


def frame(origin, u, v, *, domain=CoordinateDomain()):
    u, v = vector(u), vector(v)
    return FrameDef(origin, u, v, cross(u, v), domain)


def region(outer, holes=(), *, vertex_keys=()):
    return RegionDef(outer, holes, vertex_keys)


def box(frame, lower, upper, *, face_origins):
    return BoxDef(frame, lower, upper, face_origins)
