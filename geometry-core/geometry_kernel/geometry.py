"""Exact orthogonal region, extrusion, topology and Boolean algorithms.

No display tolerance, voxel approximation or floating point arithmetic is used.
Cells are the exact arrangement induced by source boundary coordinates.
The resource bound is explicit: exceeding it is UNSUPPORTED, never a new shape.
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field, replace
from fractions import Fraction
from itertools import product
from typing import Callable, Optional

from .errors import EvaluationError
from .types import (FrameDef, RegionDef, BoxDef, Provenance, CoordinateDomain, vector,
                    area2 as _area2, ring_location as _ring_location)


DEFAULT_MAX_CELLS = 250_000
MAX_SOURCE_FACES = 12_000
_LIMIT = 100_000_000  # Supported coordinates/dimensions, not integer storage width.
def _invalid(code, message):
    raise EvaluationError("INVALID", code, message)


def _capacity(message):
    raise EvaluationError("UNSUPPORTED", "CAPACITY", message)


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def _axes(axis):
    return tuple(i for i in range(3) if i != axis)


def _world(axis, coord, a, b):
    axes = _axes(axis)
    result = [0, 0, 0]
    result[axis] = coord
    result[axes[0]], result[axes[1]] = a, b
    return tuple(result)


@dataclass
class _Face:
    axis: int
    coord: int
    sign: int
    outer: tuple
    holes: tuple = ()
    sources: list = field(default_factory=list)
    # Preserved by dataclasses.replace when a shell changes the usage orientation.
    source_sign: Optional[int] = None
    domain: CoordinateDomain = CoordinateDomain()

    def __post_init__(self):
        region = RegionDef(self.outer, self.holes)
        self.outer, self.holes = region.outer, region.holes
        vector((self.coord, 0, 0))
        if self.source_sign is None:
            self.source_sign = self.sign
        if type(self.axis) is not int or type(self.sign) is not int or self.axis not in (0,1,2) or self.sign not in (-1,1):
            _invalid("FACE_FRAME", "Face requires an axis-aligned signed normal")
        if type(self.source_sign) is not int or self.source_sign not in (-1, 1) or any(not isinstance(source, Provenance) for source in self.sources):
            _invalid("PROVENANCE", "A face requires typed provenance and a signed source normal")
        if not isinstance(self.domain, CoordinateDomain):
            _invalid("COORDINATE_DOMAIN", "A face requires a typed coordinate domain")

    def vertices(self):
        return [_world(self.axis, self.coord, *p) for ring in (self.outer,)+self.holes for p in ring]

    def location(self, point):
        if point[self.axis] != self.coord:
            return 0
        a,b = _axes(self.axis)
        uv = (point[a],point[b])
        outer = _ring_location(uv, self.outer)
        if outer != 2:
            return outer
        for hole in self.holes:
            location = _ring_location(uv, hole)
            if location == 2:
                return 0
            if location == 1:
                return 1
        return 2


@dataclass
class _Geometry:
    # Boolean geometry retains all dependency source faces, not only visible ones.
    faces: list
    inside: Optional[Callable] = None
    domain: Optional[CoordinateDomain] = None

    def __post_init__(self):
        domains = {face.domain for face in self.faces}
        if self.domain is not None:
            domains.add(self.domain)
        if any(not isinstance(domain, CoordinateDomain) for domain in domains) or len(domains) > 1:
            _invalid("COORDINATE_DOMAIN", "A geometry cannot combine distinct coordinate domains")
        self.domain = next(iter(domains), CoordinateDomain())


def _face_vertices(vertices, sources, domain=CoordinateDomain()):
    points = tuple(tuple(p) for p in vertices)
    normals = [_cross(_sub(points[i],points[0]), _sub(points[i+1],points[0])) for i in range(1,len(points)-1)]
    normal = next((n for n in normals if any(n)), None)
    if normal is None or sum(x != 0 for x in normal) != 1:
        _invalid("FACE_DEGENERATE", "A source face must have positive area and an axis-aligned normal")
    axis = next(i for i,x in enumerate(normal) if x)
    sign = 1 if normal[axis] > 0 else -1
    coord = points[0][axis]
    if any(p[axis] != coord for p in points):
        _invalid("FACE_NONPLANAR", "A source face must be planar")
    a,b = _axes(axis)
    return _Face(axis,coord,sign,tuple((p[a],p[b]) for p in points),sources=sources,domain=domain)


def _placed_face(frame, region, height, sign, source):
    axis = next(i for i, x in enumerate(frame.n) if x)
    a, b = _axes(axis)
    def ring(points):
        return tuple((frame.world(p, height)[a], frame.world(p, height)[b]) for p in points)
    coord = frame.origin[axis] + height * frame.n[axis]
    return _Face(axis, coord, sign * frame.n[axis], ring(region.outer),
                tuple(ring(h) for h in region.holes), [source], domain=frame.domain)


def placed_region_geometry(frame, region, source):
    if not isinstance(frame, FrameDef) or not isinstance(region, RegionDef) or not isinstance(source, Provenance):
        _invalid("GEOMETRY_INPUT", "Expected validated frame, region and provenance")
    result = _Geometry([_placed_face(frame, region, 0, 1, source)])
    for face in result.faces:
        for point in face.vertices():
            vector(point)
    return result


def extrusion_span(lo, hi):
    if type(lo) is not int or type(hi) is not int or lo >= hi:
        _invalid("EXTRUSION_SPAN", "Extrusion bounds must be exact integers with lo < hi")
    if hi-lo > _LIMIT:
        _invalid("EXTRUSION_RANGE", "Extrusion thickness exceeds the supported range")


def extrusion_geometry(frame, region, lo, hi, sources):
    if not isinstance(frame, FrameDef) or not isinstance(region, RegionDef):
        _invalid("GEOMETRY_INPUT", "Expected a validated frame and region")
    extrusion_span(lo, hi)
    if any(any(value < -_LIMIT or value > _LIMIT for value in frame.world(point, height))
           for ring in (region.outer, *region.holes) for point in ring for height in (lo, hi)):
        _invalid("EXTRUSION_RANGE", "Generated world vertices exceed the supported range")
    def source(feature, loop=-1, edge=-1):
        value = sources.get((feature, loop, edge))
        if not isinstance(value, Provenance):
            _invalid("MISSING_FACE_SOURCE", "An output rectangle has no complete source-face coverage")
        return value
    faces = [_placed_face(frame, region, lo, -1, source("bottom_cap")),
             _placed_face(frame, region, hi, 1, source("top_cap"))]
    for loop_index, ring in enumerate((region.outer,) + region.holes):
        winding = 1 if _area2(ring) > 0 else -1
        for edge_index, (a, b) in enumerate(zip(ring, ring[1:] + ring[:1])):
            target = winding * (1 if loop_index == 0 else -1)
            points = [frame.world(a, lo), frame.world(b, lo), frame.world(b, hi), frame.world(a, hi)]
            if target < 0:
                points.reverse()
            faces.append(_face_vertices(points, [source("outer_side" if loop_index == 0 else "hole_side", loop_index, edge_index)], domain=frame.domain))
    if any(any(v < -_LIMIT or v > _LIMIT for v in p) for f in faces for p in f.vertices()):
        _invalid("EXTRUSION_RANGE", "Generated world vertices exceed the supported range")
    def inside(point):
        local = _sub(point, frame.origin)
        h = _dot(local, frame.n)
        uv = (_dot(local, frame.u), _dot(local, frame.v))
        return lo < h < hi and region.location(uv) == 2
    return _Geometry(faces, inside)


def box_geometry(definition):
    if not isinstance(definition, BoxDef):
        _invalid("GEOMETRY_INPUT", "Expected a validated box definition")
    frame, lower, upper = definition.frame, definition.lower, definition.upper
    faces = []
    for axis in range(3):
        a, b = _axes(axis)
        for side, sign in enumerate((-1, 1)):
            coord = (lower, upper)[side][axis]
            rectangle = _rectangle(axis, coord, sign, lower[a], upper[a], lower[b], upper[b])
            points = [frame.world(p[:2], p[2]) for p in rectangle]
            faces.append(_face_vertices(points, [definition.face_origins[2*axis+side]], domain=frame.domain))
    def inside(point):
        delta = _sub(point, frame.origin)
        local = tuple(_dot(delta, axis) for axis in (frame.u, frame.v, frame.n))
        return all(lo < value < hi for lo, value, hi in zip(lower, local, upper))
    return _Geometry(faces, inside)


@dataclass(frozen=True)
class _Arrangement:
    axes: tuple
    domain: CoordinateDomain

    def __iter__(self):
        return iter(self.axes)

    def __getitem__(self, index):
        return self.axes[index]

    def __len__(self):
        return len(self.axes)


def build_grid(geometries, max_cells=DEFAULT_MAX_CELLS):
    """Build exact coordinate cuts bound to one coordinate domain."""
    if type(max_cells) is not int or max_cells < 1:
        _capacity("The exact arrangement cell limit must be a positive integer")
    geometries = tuple(geometries)
    if len({geometry.domain for geometry in geometries}) > 1:
        _invalid("COORDINATE_DOMAIN", "An exact arrangement cannot mix coordinate domains")
    coords = [set(),set(),set()]
    for geometry in geometries:
        for face in geometry.faces:
            for point in face.vertices():
                for axis,value in enumerate(point):
                    coords[axis].add(value)
    grid = tuple(tuple(sorted(c)) for c in coords)
    count = 1
    for axis in grid:
        count *= max(0,len(axis)-1)
    if count > max_cells:
        _capacity(f"Exact arrangement requires {count} cells; configured limit is {max_cells}")
    return _Arrangement(grid, next((geometry.domain for geometry in geometries), CoordinateDomain()))


def _rectangle(axis,coord,sign,alo,ahi,blo,bhi):
    points = [_world(axis,coord,alo,blo),_world(axis,coord,ahi,blo),_world(axis,coord,ahi,bhi),_world(axis,coord,alo,bhi)]
    normal = _cross(_sub(points[1],points[0]),_sub(points[2],points[0]))
    if (normal[axis] > 0) != (sign > 0):
        points.reverse()
    start = min(range(4),key=lambda i:points[i])
    return tuple(points[start:]+points[:start])


def _face_patches(face,grid):
    a,b = _axes(face.axis)
    amin,amax = min(p[0] for p in face.outer),max(p[0] for p in face.outer)
    bmin,bmax = min(p[1] for p in face.outer),max(p[1] for p in face.outer)
    ai = [i for i in range(len(grid[a])-1) if amin <= grid[a][i] and grid[a][i+1] <= amax]
    bi = [i for i in range(len(grid[b])-1) if bmin <= grid[b][i] and grid[b][i+1] <= bmax]
    for i,j in product(ai,bi):
        alo,ahi = grid[a][i:i+2]
        blo,bhi = grid[b][j:j+2]
        center = _world(face.axis,face.coord,Fraction(alo+ahi,2),Fraction(blo+bhi,2))
        if face.location(center) == 2:
            yield (face.axis,face.coord,i,j),_rectangle(face.axis,face.coord,face.sign,alo,ahi,blo,bhi)


def _triangles(patches):
    return [(p[0],p[1],p[2]) for p in patches]+[(p[0],p[2],p[3]) for p in patches]


def _signed_volume(triangles):
    six = sum(_dot(a,_cross(b,c)) for a,b,c in triangles)
    return Fraction(six,6)


def _mesh_topology(triangles, require_connected=False):
    """Full edge and vertex-link checks, including disconnected vertex pinches."""
    edges = defaultdict(list)
    links = defaultdict(lambda:defaultdict(list))
    adjacent = [set() for _ in triangles]
    for ti,tri in enumerate(triangles):
        if len(set(tri)) != 3:
            _invalid("SHELL_DEGENERATE", "A shell contains a degenerate triangle")
        for a,b in zip(tri,tri[1:]+tri[:1]):
            edges[tuple(sorted((a,b)))].append((ti,a,b))
        for i,v in enumerate(tri):
            a,b = tri[(i+1)%3],tri[(i+2)%3]
            links[v][a].append(b)
            links[v][b].append(a)
    boundary = []
    for edge,uses in edges.items():
        if len(uses) > 2:
            _invalid("SHELL_NONMANIFOLD_EDGE", "More than two faces use a shell edge")
        if len(uses) == 2:
            u,v = uses
            if u[1:] != (v[2],v[1]):
                _invalid("SHELL_ORIENTATION", "Adjacent shell faces traverse their common edge in the same direction")
            adjacent[u[0]].add(v[0]); adjacent[v[0]].add(u[0])
        else:
            boundary.append(edge)
    for vertex,link in links.items():
        degrees = [len(n) for n in link.values()]
        if any(d not in (1,2) for d in degrees) or degrees.count(1) not in (0,2):
            _invalid("SHELL_VERTEX_LINK", f"Shell vertex {vertex} has no single path/cycle link")
        seen = set()
        todo = [next(iter(link))]
        while todo:
            node = todo.pop()
            if node in seen:
                continue
            seen.add(node); todo.extend(link[node])
        if len(seen) != len(link):
            _invalid("SHELL_VERTEX_PINCH", f"Shell vertex {vertex} joins disconnected face fans")
    groups = []
    unseen = set(range(len(triangles)))
    while unseen:
        todo = [min(unseen)]; group = []
        while todo:
            current = todo.pop()
            if current not in unseen:
                continue
            unseen.remove(current); group.append(current); todo.extend(adjacent[current])
        groups.append(sorted(group))
    if require_connected and len(groups) != 1:
        _invalid("SHELL_DISCONNECTED", "A boundary shell must be connected through shared edges")
    return sorted(boundary),groups


def _check_intersections(faces,grid):
    # Coplanar interior overlaps are checked by duplicate arrangement rectangles.
    occupied = set()
    for face in faces:
        for key,_ in _face_patches(face,grid):
            if key in occupied:
                _invalid("SHELL_FACE_OVERLAP", "Shell face interiors overlap")
            occupied.add(key)
    # A perpendicular intersection must be on BOTH original polygon boundaries.
    # Test atomic line intervals and their endpoints; all intersection coordinates
    # are in the exact grid, so a face crossing cannot hide between samples.
    for i,first in enumerate(faces):
        for second in faces[i+1:]:
            if first.axis == second.axis:
                continue
            third = next(a for a in range(3) if a not in (first.axis,second.axis))
            samples = list(grid[third])+[Fraction(a+b,2) for a,b in zip(grid[third],grid[third][1:])]
            point = [0,0,0]
            point[first.axis],point[second.axis] = first.coord,second.coord
            for value in samples:
                point[third] = value
                one,two = first.location(point),second.location(point)
                if one and two and (one == 2 or two == 2):
                    _invalid("SHELL_SELF_INTERSECTION", "Shell faces intersect through a face interior")


def analyze_shell(faces, max_cells=DEFAULT_MAX_CELLS):
    if not faces:
        _invalid("SHELL_EMPTY", "A shell requires at least one face")
    grid = build_grid([_Geometry(faces)],max_cells)
    _check_intersections(faces,grid)
    patches = []
    for face in faces:
        patches.extend(patch for _,patch in _face_patches(face,grid))
        if len(patches) > 6*max_cells:
            _capacity("Shell arrangement exceeds the configured surface capacity")
    triangles = _triangles(patches)
    boundary,groups = _mesh_topology(triangles,require_connected=True)
    closed = not boundary
    volume = _signed_volume(triangles) if closed else None
    if closed and not volume:
        _invalid("SHELL_ZERO_VOLUME", "A closed shell must bound nonzero volume")
    return {"closed":closed,"signed_volume":volume,"boundary_edges":[[list(a),list(b)] for a,b in boundary]}


def enclosed_geometry(faces, max_cells=DEFAULT_MAX_CELLS):
    analysis = analyze_shell(faces,max_cells)
    if not analysis["closed"]:
        raise EvaluationError("INCOMPLETE","OPEN_SHELL","An open shell has no determined enclosed volume")
    if analysis["signed_volume"] <= 0:
        _invalid("SHELL_INWARD", "An interior boundary must face out of its enclosed volume")
    ray_faces = [f for f in faces if f.axis == 0]
    def inside(point):
        intersections = 0
        for face in ray_faces:
            if face.coord > point[0] and face.location((face.coord,point[1],point[2])) == 2:
                intersections += 1
        return intersections % 2 == 1
    return _Geometry(faces,inside)


def boolean_geometry(op, operands, *, max_source_faces=MAX_SOURCE_FACES):
    if len({geometry.domain for geometry in operands}) > 1:
        _invalid("COORDINATE_DOMAIN", "Boolean inputs must use the same coordinate domain")
    if any(g.inside is None for g in operands):
        _invalid("BOOLEAN_NOT_SOLID", "Boolean operands must all be solved solid sets")
    # A shallow spatial grid does not bound the number of provenance paths in a
    # shared dependency DAG. Check before concatenation, preserving every path
    # below the limit and refusing an expansion rather than dropping sources.
    source_face_count = sum(len(g.faces) for g in operands)
    if type(max_source_faces) is not int or max_source_faces < 1:
        _capacity("The source-face limit must be a positive integer")
    if source_face_count > max_source_faces:
        _capacity(f"Boolean provenance requires {source_face_count} source faces; configured limit is {max_source_faces}")
    if op == "UNION":
        inside = lambda p:any(g.inside(p) for g in operands)
    elif op == "DIFFERENCE" and operands:
        inside = lambda p:operands[0].inside(p) and not any(g.inside(p) for g in operands[1:])
    else:
        _invalid("BOOLEAN_OPERATION", "Unknown or invalid solid composition operation")
    return _Geometry([f for g in operands for f in g.faces],inside,
                     domain=operands[0].domain if operands else CoordinateDomain())


def prefix_geometry(geometry, path=(), contribution=None):
    if not path and contribution is None:
        return geometry
    return replace(geometry, faces=tuple(replace(face, sources=tuple(
        source.prefixed(path, contribution=contribution) for source in face.sources)) for face in geometry.faces))


def _source_key(source):
    return source.sort_key


def _patch_sources(axis,coord,sign,patch,face_index):
    center = tuple(Fraction(a+b,2) for a,b in zip(patch[0],patch[2]))
    records = []
    seen = set()
    for face in face_index.get((axis,coord),[]):
        if face.location(center) != 2:
            continue
        for source in face.sources:
            record = replace(source, normal_sign=sign*face.source_sign)
            fingerprint = record
            if fingerprint not in seen:
                seen.add(fingerprint); records.append(record)
    if not records:
        _invalid("MISSING_FACE_SOURCE", "An output rectangle has no complete source-face coverage")
    return sorted(records,key=_source_key)


def _mesh_record(patches,face_index,component,volume,require_closed):
    records = []
    for axis,coord,sign,patch in patches:
        sources = _patch_sources(axis,coord,sign,patch,face_index)
        source_key = tuple((_source_key(s),s.normal_sign) for s in sources)
        records.append(((patch[0],patch[1],patch[2]),sources,source_key))
        records.append(((patch[0],patch[2],patch[3]),sources,source_key))
    records.sort(key=lambda r:(r[0],r[2]))
    triangles = [r[0] for r in records]
    boundary,groups = _mesh_topology(triangles)
    if require_closed and boundary:
        _invalid("SOLID_OPEN_BOUNDARY", "A solid component has an open boundary")
    boundary_shells = []
    for group in groups:
        selected = [triangles[i] for i in group]
        group_boundary,_ = _mesh_topology(selected)
        signed = _signed_volume(selected)
        shell_role = "open" if group_boundary else ("outer" if signed > 0 else "cavity")
        if require_closed and (group_boundary or signed == 0):
            _invalid("SOLID_SHELL", "A solid boundary shell must be closed with nonzero signed volume")
        boundary_shells.append({"id":len(boundary_shells),"role":shell_role,"triangles":group})
    if require_closed:
        computed = _signed_volume(triangles)
        if computed != volume or computed <= 0:
            _invalid("SOLID_VOLUME", "Boundary orientation and exact occupied-cell volume disagree")
    vertices = sorted({p for tri in triangles for p in tri})
    indexes = {p:i for i,p in enumerate(vertices)}
    return {
        "status":"COMPLETE",
        "representation":"mesh","closure":"open" if boundary else "closed","component":component,
        "vertices_mm":[list(p) for p in vertices],"triangles":[[indexes[p] for p in tri] for tri in triangles],
        "face_sources":[r[1] for r in records],"boundary_shells":boundary_shells,
        "volume_mm3":None if volume is None else str(volume),
    }


def mesh_objects(geometry, grid, *, volume_known=None, max_cells=DEFAULT_MAX_CELLS):
    """Canonical meshes, including all cavity shells and disjoint volumes.

    `volume_known=False` preserves the zero-thickness semantics of a shell even
    when an executor has separately proved that the shell encloses a volume.
    """
    if not isinstance(grid, _Arrangement) or grid.domain != geometry.domain:
        _invalid("COORDINATE_DOMAIN", "A mesh requires an arrangement from its coordinate domain")
    if not geometry.faces:
        return [{"status":"EMPTY","representation":"mesh","closure":"empty","component":None,"vertices_mm":[],"triangles":[],"face_sources":[],"boundary_shells":[],"volume_mm3":None if geometry.inside is None else "0"}]
    face_index = defaultdict(list)
    for face in geometry.faces:
        face_index[(face.axis,face.coord)].append(face)
    if geometry.inside is None:
        patches = []
        for face in geometry.faces:
            for _,patch in _face_patches(face,grid):
                patches.append((face.axis,face.coord,face.sign,patch))
                if len(patches) > 6*max_cells:
                    _capacity("Surface output exceeds the configured capacity")
        return [_mesh_record(patches,face_index,None,None,False)]
    dimensions = tuple(max(0,len(g)-1) for g in grid)
    cell_count = dimensions[0]*dimensions[1]*dimensions[2]
    if cell_count > max_cells:
        _capacity(f"Exact arrangement requires {cell_count} cells; configured limit is {max_cells}")
    occupied = set()
    for cell in product(*(range(n) for n in dimensions)):
        center = tuple(Fraction(grid[a][i]+grid[a][i+1],2) for a,i in enumerate(cell))
        if geometry.inside(center):
            occupied.add(cell)
    if not occupied:
        return [{"status":"EMPTY","representation":"mesh","closure":"empty","component":None,"vertices_mm":[],"triangles":[],"face_sources":[],"boundary_shells":[],"volume_mm3":"0"}]
    components = []
    remaining = set(occupied)
    while remaining:
        seed = min(remaining)
        todo = deque([seed]); cells = set()
        remaining.remove(seed)
        while todo:
            cell = todo.popleft(); cells.add(cell)
            for axis in range(3):
                for sign in (-1,1):
                    neighbor = tuple(v+(sign if a == axis else 0) for a,v in enumerate(cell))
                    if neighbor in remaining:
                        remaining.remove(neighbor); todo.append(neighbor)
        components.append(cells)
    objects = []
    for component,cells in enumerate(components):
        patches = []
        volume = 0
        for cell in sorted(cells):
            sizes = [grid[a][i+1]-grid[a][i] for a,i in enumerate(cell)]
            volume += sizes[0]*sizes[1]*sizes[2]
            for axis in range(3):
                a,b = _axes(axis)
                for sign in (-1,1):
                    neighbor = tuple(v+(sign if d == axis else 0) for d,v in enumerate(cell))
                    if neighbor in occupied:
                        continue
                    coord = grid[axis][cell[axis]+(1 if sign > 0 else 0)]
                    patch = _rectangle(axis,coord,sign,grid[a][cell[a]],grid[a][cell[a]+1],grid[b][cell[b]],grid[b][cell[b]+1])
                    patches.append((axis,coord,sign,patch))
        record = _mesh_record(patches,face_index,component,volume,True)
        if volume_known is False:
            record["volume_mm3"] = None
        objects.append(record)
    return objects
