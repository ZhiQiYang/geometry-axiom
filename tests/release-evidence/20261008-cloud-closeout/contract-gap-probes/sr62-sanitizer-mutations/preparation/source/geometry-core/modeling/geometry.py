"""Exact orthogonal geometry and canonical meshes for orthogonal-model/1.

No display tolerance, voxel approximation or floating point arithmetic is used.
Cells are the exact arrangement induced by source boundary coordinates (R27/R29).
The resource bound is explicit: exceeding it is UNSUPPORTED, never a new shape.
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from fractions import Fraction
from itertools import product
from typing import Callable, Optional

from .common import ModelError


DEFAULT_MAX_CELLS = 250_000
MAX_SOURCE_FACES = 12_000
_LIMIT = 100_000_000  # D1 supported coordinates/dimensions, not int64 storage width.
_SOURCE_FIELDS = (
    "origin", "feature", "placement_id", "boundary_id", "loop_index",
    "edge_index", "operation_path", "role", "normal_sign",
)


def _invalid(code, clause, message):
    raise ModelError("INVALID", code, clause, message)


def _capacity(message):
    raise ModelError("UNSUPPORTED", "CAPACITY", "I33", message)


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


def _area2(ring):
    return sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(ring, ring[1:]+ring[:1]))


def _ring_location(point, ring):
    """0 outside, 1 on boundary, 2 strictly inside; exact even/odd test."""
    x, y = point
    inside = False
    for a, b in zip(ring, ring[1:]+ring[:1]):
        cross = (x-a[0])*(b[1]-a[1])-(y-a[1])*(b[0]-a[0])
        if cross == 0 and min(a[0],b[0]) <= x <= max(a[0],b[0]) and min(a[1],b[1]) <= y <= max(a[1],b[1]):
            return 1
        if (a[1] > y) != (b[1] > y):
            intersect = a[0] + Fraction(b[0]-a[0], b[1]-a[1])*(y-a[1])
            if x < intersect:
                inside = not inside
    return 2 if inside else 0


@dataclass
class Face:
    axis: int
    coord: int
    sign: int
    outer: tuple
    holes: tuple = ()
    sources: list = field(default_factory=list)
    # Preserved by dataclasses.replace when a shell changes the usage orientation.
    source_sign: Optional[int] = None

    def __post_init__(self):
        self.outer = tuple(tuple(p) for p in self.outer)
        self.holes = tuple(tuple(tuple(p) for p in ring) for ring in self.holes)
        if self.source_sign is None:
            self.source_sign = self.sign
        if self.axis not in (0,1,2) or self.sign not in (-1,1):
            _invalid("FACE_FRAME", "D2", "Face requires an axis-aligned signed normal")

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
class Geometry:
    # Boolean geometry retains all dependency source faces, not only visible ones.
    faces: list
    inside: Optional[Callable] = None


def _source(source, feature, placement_id=None, boundary_id=None, loop_index=-1, edge_index=-1):
    return {
        "origin": dict(source["origin"]), "feature": feature,
        "placement_id": placement_id, "boundary_id": boundary_id,
        "loop_index": loop_index, "edge_index": edge_index,
        "operation_path": list(source.get("operation_path", [])),
        "role": source.get("role", "boundary"), "normal_sign": 1,
    }


def _face_vertices(vertices, sources):
    points = tuple(tuple(p) for p in vertices)
    normals = [_cross(_sub(points[i],points[0]), _sub(points[i+1],points[0])) for i in range(1,len(points)-1)]
    normal = next((n for n in normals if any(n)), None)
    if normal is None or sum(x != 0 for x in normal) != 1:
        _invalid("FACE_DEGENERATE", "I1", "A source face must have positive area and an axis-aligned normal")
    axis = next(i for i,x in enumerate(normal) if x)
    sign = 1 if normal[axis] > 0 else -1
    coord = points[0][axis]
    if any(p[axis] != coord for p in points):
        _invalid("FACE_NONPLANAR", "I1", "A source face must be planar")
    a,b = _axes(axis)
    return Face(axis,coord,sign,tuple((p[a],p[b]) for p in points),sources=sources)


def _placement_world(placement, uv, height=0):
    return tuple(placement["origin"][i]+uv[0]*placement["u"][i]+uv[1]*placement["v"][i]+height*placement["n"][i] for i in range(3))


def _placement_face(placement, height, sign, source):
    n = placement["n"]
    axis = next(i for i,x in enumerate(n) if x)
    a,b = _axes(axis)
    def ring(points):
        return tuple((_placement_world(placement,p,height)[a],_placement_world(placement,p,height)[b]) for p in points)
    coord = placement["origin"][axis]+height*n[axis]
    return Face(axis,coord,sign*n[axis],ring(placement["outline"]),tuple(ring(h) for h in placement["holes"]),[source])


def placement_geometry(placement, source):
    """A placed local D3 region, with its actual holes, in its D4 world frame."""
    s = _source(source,"surface",placement["id"],placement.get("boundary_id"))
    return Geometry([_placement_face(placement,0,1,s)])


def extrusion_geometry(placement, lo, hi, source):
    if not isinstance(lo,int) or isinstance(lo,bool) or not isinstance(hi,int) or isinstance(hi,bool) or lo >= hi:
        _invalid("EXTRUSION_SPAN", "I26", "Extrusion bounds must be exact integers with lo < hi")
    if hi-lo > _LIMIT:
        _invalid("EXTRUSION_RANGE", "I26", "Extrusion thickness exceeds the D1 range")
    def s(feature,loop=-1,edge=-1):
        return _source(source,feature,placement["id"],placement.get("boundary_id"),loop,edge)
    faces = [_placement_face(placement,lo,-1,s("bottom_cap")),_placement_face(placement,hi,1,s("top_cap"))]
    # Preserve original edge indexes even when the source winding is reversed.
    for loop_index, ring in enumerate([placement["outline"]]+placement["holes"]):
        ring = tuple(tuple(p) for p in ring)
        winding = 1 if _area2(ring) > 0 else -1
        for edge_index,(a,b) in enumerate(zip(ring,ring[1:]+ring[:1])):
            # For CCW outer ring, right-hand edge normal is outside material;
            # for a hole it is the reverse. U/V/N is a right-handed frame.
            target = winding * (1 if loop_index == 0 else -1)
            points = [_placement_world(placement,a,lo),_placement_world(placement,b,lo),_placement_world(placement,b,hi),_placement_world(placement,a,hi)]
            if target < 0:
                points.reverse()
            faces.append(_face_vertices(points,[s("outer_side" if loop_index == 0 else "hole_side",loop_index,edge_index)]))
    if any(any(v < -_LIMIT or v > _LIMIT for v in p) for f in faces for p in f.vertices()):
        _invalid("EXTRUSION_RANGE", "I26", "Generated world vertices exceed the D1 supported range")
    origin,u,v,n = (tuple(placement[k]) for k in ("origin","u","v","n"))
    outline = tuple(tuple(p) for p in placement["outline"])
    holes = tuple(tuple(tuple(p) for p in h) for h in placement["holes"])
    def inside(point):
        local = _sub(point,origin)
        h = _dot(local,n)
        uv = (_dot(local,u),_dot(local,v))
        return lo < h < hi and _ring_location(uv,outline) == 2 and all(_ring_location(uv,hole) == 0 for hole in holes)
    return Geometry(faces,inside)


def solid_geometry(solid, source):
    faces = [_face_vertices(f["vertices"],[_source(source,f["feature"],solid.get("placement_id"),solid.get("boundary_id"))]) for f in solid["faces"]]
    bounds = [(min(p[a] for f in faces for p in f.vertices()),max(p[a] for f in faces for p in f.vertices())) for a in range(3)]
    # C bridge emits validated axis-aligned column/beam/timber boxes, not meshes.
    if len(faces) != 6 or any(lo >= hi for lo,hi in bounds):
        _invalid("BASE_SOLID", "D7", "A base solid must provide six nondegenerate box faces")
    return Geometry(faces,lambda point: all(lo < point[a] < hi for a,(lo,hi) in enumerate(bounds)))


def build_grid(geometries, max_cells=DEFAULT_MAX_CELLS):
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
    return grid


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
            _invalid("SHELL_DEGENERATE", "I27", "A shell contains a degenerate triangle")
        for a,b in zip(tri,tri[1:]+tri[:1]):
            edges[tuple(sorted((a,b)))].append((ti,a,b))
        for i,v in enumerate(tri):
            a,b = tri[(i+1)%3],tri[(i+2)%3]
            links[v][a].append(b)
            links[v][b].append(a)
    boundary = []
    for edge,uses in edges.items():
        if len(uses) > 2:
            _invalid("SHELL_NONMANIFOLD_EDGE", "I27", "More than two faces use a shell edge")
        if len(uses) == 2:
            u,v = uses
            if u[1:] != (v[2],v[1]):
                _invalid("SHELL_ORIENTATION", "I27", "Adjacent shell faces traverse their common edge in the same direction")
            adjacent[u[0]].add(v[0]); adjacent[v[0]].add(u[0])
        else:
            boundary.append(edge)
    for vertex,link in links.items():
        degrees = [len(n) for n in link.values()]
        if any(d not in (1,2) for d in degrees) or degrees.count(1) not in (0,2):
            _invalid("SHELL_VERTEX_LINK", "I27", f"Shell vertex {vertex} has no single path/cycle link")
        seen = set()
        todo = [next(iter(link))]
        while todo:
            node = todo.pop()
            if node in seen:
                continue
            seen.add(node); todo.extend(link[node])
        if len(seen) != len(link):
            _invalid("SHELL_VERTEX_PINCH", "I27", f"Shell vertex {vertex} joins disconnected face fans")
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
        _invalid("SHELL_DISCONNECTED", "I27", "A boundary shell must be connected through shared edges")
    return sorted(boundary),groups


def _check_intersections(faces,grid):
    # Coplanar interior overlaps are checked by duplicate arrangement rectangles.
    occupied = set()
    for face in faces:
        for key,_ in _face_patches(face,grid):
            if key in occupied:
                _invalid("SHELL_FACE_OVERLAP", "I27", "Shell face interiors overlap")
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
                    _invalid("SHELL_SELF_INTERSECTION", "I27", "Shell faces intersect through a face interior")


def analyze_shell(faces, max_cells=DEFAULT_MAX_CELLS):
    if not faces:
        _invalid("SHELL_EMPTY", "D21", "A shell requires at least one face")
    grid = build_grid([Geometry(faces)],max_cells)
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
        _invalid("SHELL_ZERO_VOLUME", "I28", "A closed shell must bound nonzero volume")
    return {"closed":closed,"signed_volume":volume,"boundary_edges":[[list(a),list(b)] for a,b in boundary]}


def enclosed_geometry(faces, max_cells=DEFAULT_MAX_CELLS):
    analysis = analyze_shell(faces,max_cells)
    if not analysis["closed"]:
        raise ModelError("INCOMPLETE","OPEN_SHELL","I28","An open shell has no determined enclosed volume")
    if analysis["signed_volume"] <= 0:
        _invalid("SHELL_INWARD", "I28", "A composite space shell must face out of its enclosed volume")
    ray_faces = [f for f in faces if f.axis == 0]
    def inside(point):
        intersections = 0
        for face in ray_faces:
            if face.coord > point[0] and face.location((face.coord,point[1],point[2])) == 2:
                intersections += 1
        return intersections % 2 == 1
    return Geometry(faces,inside)


def boolean_geometry(op, operands):
    if any(g.inside is None for g in operands):
        _invalid("BOOLEAN_NOT_SOLID", "I29", "Boolean operands must all be solved solid sets")
    # A shallow spatial grid does not bound the number of provenance paths in a
    # shared dependency DAG. Check before concatenation, preserving every path
    # below the limit and refusing an expansion rather than dropping sources.
    source_face_count = sum(len(g.faces) for g in operands)
    if source_face_count > MAX_SOURCE_FACES:
        _capacity(f"Boolean provenance requires {source_face_count} source faces; configured limit is {MAX_SOURCE_FACES}")
    if op == "UNION":
        inside = lambda p:any(g.inside(p) for g in operands)
    elif op == "DIFFERENCE" and operands:
        inside = lambda p:operands[0].inside(p) and not any(g.inside(p) for g in operands[1:])
    else:
        _invalid("BOOLEAN_OPERATION", "D23", "Unknown or invalid solid composition operation")
    return Geometry([f for g in operands for f in g.faces],inside)


def _source_key(source):
    return (source["origin"]["kind"],source["origin"]["id"],source["feature"],source["loop_index"],source["edge_index"],tuple(source["operation_path"]),source["role"])


def _patch_sources(axis,coord,sign,patch,face_index):
    center = tuple(Fraction(a+b,2) for a,b in zip(patch[0],patch[2]))
    records = []
    seen = set()
    for face in face_index.get((axis,coord),[]):
        if face.location(center) != 2:
            continue
        for source in face.sources:
            record = {k:source[k] for k in _SOURCE_FIELDS}
            record["normal_sign"] = sign*face.source_sign
            fingerprint = (_source_key(record),record["placement_id"],record["boundary_id"],record["normal_sign"])
            if fingerprint not in seen:
                seen.add(fingerprint); records.append(record)
    if not records:
        _invalid("MISSING_FACE_SOURCE", "R28", "An output rectangle has no complete source-face coverage")
    return sorted(records,key=_source_key)


def _mesh_record(patches,face_index,root,member_path,role,component,volume,require_closed):
    records = []
    for axis,coord,sign,patch in patches:
        sources = _patch_sources(axis,coord,sign,patch,face_index)
        source_key = tuple((_source_key(s),s["normal_sign"]) for s in sources)
        records.append(((patch[0],patch[1],patch[2]),sources,source_key))
        records.append(((patch[0],patch[2],patch[3]),sources,source_key))
    records.sort(key=lambda r:(r[0],r[2]))
    triangles = [r[0] for r in records]
    boundary,groups = _mesh_topology(triangles)
    if require_closed and boundary:
        _invalid("SOLID_OPEN_BOUNDARY", "I28", "A solid component has an open boundary")
    boundary_shells = []
    for group in groups:
        selected = [triangles[i] for i in group]
        group_boundary,_ = _mesh_topology(selected)
        signed = _signed_volume(selected)
        shell_role = "open" if group_boundary else ("outer" if signed > 0 else "cavity")
        if require_closed and (group_boundary or signed == 0):
            _invalid("SOLID_SHELL", "I28", "A solid boundary shell must be closed with nonzero signed volume")
        boundary_shells.append({"id":len(boundary_shells),"role":shell_role,"triangles":group})
    if require_closed:
        computed = _signed_volume(triangles)
        if computed != volume or computed <= 0:
            _invalid("SOLID_VOLUME", "I28", "Boundary orientation and exact occupied-cell volume disagree")
    vertices = sorted({p for tri in triangles for p in tri})
    indexes = {p:i for i,p in enumerate(vertices)}
    return {
        "root":dict(root),"member_path":list(member_path),"role":role,"status":"COMPLETE",
        "representation":"mesh","closure":"open" if boundary else "closed","component":component,
        "vertices_mm":[list(p) for p in vertices],"triangles":[[indexes[p] for p in tri] for tri in triangles],
        "face_sources":[r[1] for r in records],"boundary_shells":boundary_shells,
        "volume_mm3":None if volume is None else str(volume),
    }


def mesh_objects(geometry, grid, root, member_path=None, role="geometry", volume_known=None, max_cells=DEFAULT_MAX_CELLS):
    """Canonical R29 objects, including all cavity shells and disjoint volumes.

    `volume_known=False` preserves the zero-thickness semantics of a shell even
    when an executor has separately proved that the shell encloses a volume.
    """
    member_path = [] if member_path is None else member_path
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
        return [_mesh_record(patches,face_index,root,member_path,role,None,None,False)]
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
        return [{"root":dict(root),"member_path":list(member_path),"role":role,"status":"EMPTY","representation":"mesh","closure":"empty","component":None,"vertices_mm":[],"triangles":[],"face_sources":[],"boundary_shells":[],"volume_mm3":"0"}]
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
        record = _mesh_record(patches,face_index,root,member_path,role,component,volume,True)
        if volume_known is False:
            record["volume_mm3"] = None
        objects.append(record)
    return objects
