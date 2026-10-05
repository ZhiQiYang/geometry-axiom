# T4: shared rooms retain each reference view

This repair restores the existing per-face display behavior in REFERENCE-PROJECT.md.
The shared source plane owns calibration and alignment. Each room owns crop,
opacity and lock. Display changes do not change native geometry, create recognition
results, introduce new review rules, or add a UI entry.

## Finite representation

`source-rooms/3` retains the existing planes, collections and rooms. Every room
has a mandatory closed `display` object containing exactly `crop`, `opacity`,
and `locked`. Optional `legacyHistory` must be nonempty and retains the existing
/2 closed history validation, original extensible records and reconstruction
receipt rules. Neither calibration nor alignment may appear in room.display.

The reader-only capability is `source-room-display/1`, in addition to
`source-room-collection/1` and, when history exists, `source-room-history/1`.
The existing root feature format is used; no new root .gcanvas version is allocated.
Capability stripping for native verification uses the common reader registry.
An older reader must reject the unknown attachment or capability before mutation.

`reference-display.js` validates both ordinary ReferencePage views and shared room
views. Crop is `[x,y,w,h]`, all finite, x/y nonnegative, w/h positive and inside
the original page dimensions with the existing .001 tolerance. Opacity is finite
in [0,1]; lock is boolean. Unknown fields and wrong types reject. Existing limits
remain: 256 planes, 10000 rooms, 10000 history entries, 8MiB attachment, bounded
JSON traversal, lifecycle reserve, and the whole-project/ZIP admission policies.

## Legacy and lifecycle

/1 and /2 retain their closed shapes and are still readable. Their missing display
uses the existing full-page/.5/unlocked defaults. No historical lost value is
guessed. Explicit adoption or a changed display upgrades all rooms to /3 while
retaining history. A no-op does not upgrade or add history.

Adoption copies the explicitly selected page's view before removing that old
independent basis page. Newly created rooms use the existing defaults. Editing or
reassociating an existing room preserves its view. Common basis changes preserve
every room's separate display. All writes use the common detached feature
validation/capacity admission and one ContextHistory step; they set dirty/revision.
Undo/redo and real ZIP Open reconstruct the authoritative persisted view.

The page cache signature includes plane and persisted room display. A bounded
cache of derived raster strings uses original source hash/page/dimensions and
is populated only after prepare's context/revision guard. Pure materialization
does not read private contexts or native history and does not fetch sources.
No cache contains authoritative view metadata or serialized renderer URLs.

## Verification boundaries

`tests/test_shared_room_display.js` exercises strict schema/legacy migration,
the actual registry, native capability separation, real ZIP/original PDF closure,
history retention, basis changes and retired IDs. `test_room_collection.js`
also exercises view preservation across real native edits/reassociation.

`tests/test_shared_room_display_browser.js` is a separate required gate, not an
aggregate Node suite. It checks 1280/390 normal adoption/cancel/manual new-room,
opacity/lock/alignment controls, real Undo/Redo, actual downloaded ZIP, a real
new empty context and normal Open, plus unknown schema, missing capability,
wrong display and capacity rejection with complete-state equality. Original crop
is an explicit repo-authored fixture; pointer crop import is covered separately
by #48's formal evidence gate. OS pickers and physical mobile are not claimed.

See tests/INTEGRATION-GATES.md for reproduction. A full aggregate census found
five added Node tests, so the Node floor increases 520 to 525; other floors stay.
Each final acceptance report must name its exact source and own terminal results.
