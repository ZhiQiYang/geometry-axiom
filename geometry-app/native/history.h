#ifndef GEO_APP_HISTORY_H
#define GEO_APP_HISTORY_H

#include <stdbool.h>
#include <stddef.h>

/* H owns whole-document snapshots. The buffers belong to the caller, must
 * remain alive, and must not overlap each other or the current document.
 * snapshot_size and capacity are positive; each stack has capacity complete
 * snapshots, and each backup has one. Initialization is a trusted host step.
 * No allocation, geometry, template policy, revision or presentation rules
 * live here. The product keeps its existing 32-entry static World buffers.
 * Both stacks are rings (GEO-381), with unchanged logical capacity. Undo's
 * physical ring has capacity+1 slots: slots [0,capacity) are in undo and the
 * last is the existing evicted buffer. At full record the oldest stays in
 * the spare slot before the new head; the new snapshot is the only copy.
 * A matching unrecord rewinds head without copying. Redo has capacity slots.
 * Zero heads are the initial state. Physical buffer contents/locations are
 * private; read the latest undo snapshot through app_history_peek_undo.
 * unrecord must match record, before another mutating history operation;
 * peek_undo may read that record to restore a failed command's document.
 * Invariant: every public operation keeps undo_count + redo_count <= capacity
 * (record empties redo; undo and redo move one entry between the stacks;
 * unrecord restores the counts from before the matching record; clear empties
 * both). So the full-stack branches in undo (redo full) and redo (undo full)
 * cannot run through this API; they are kept only as a defensive bound, and
 * redo_head stays 0 in every reachable state. */
typedef struct {
    size_t snapshot_size, capacity;
    unsigned char *undo, *redo, *evicted, *group_base;
    size_t undo_count, redo_count, record_redo_count;
    bool record_evicted, grouping, group_dirty;
    size_t undo_head, redo_head;
} AppHistory;

/* The caller's restore hook cannot fail. It implements any presentation merge;
 * group abort and failed-operation rollback use complete snapshots instead. */
typedef void (*AppHistoryRestore)(void *document, const void *snapshot, void *opaque);

void app_history_init(AppHistory *, size_t snapshot_size, size_t capacity,
    void *undo, void *redo, void *evicted, void *group_base);
void app_history_record(AppHistory *, const void *document);
void app_history_unrecord(AppHistory *);
void app_history_clear(AppHistory *);
const void *app_history_peek_undo(const AppHistory *);
bool app_history_undo(AppHistory *, void *document, AppHistoryRestore, void *opaque);
bool app_history_redo(AppHistory *, void *document, AppHistoryRestore, void *opaque);
bool app_history_group_begin(AppHistory *, const void *document);
void app_history_group_mark_dirty(AppHistory *);
/* The caller performs its existing domain validation before committing a group. */
bool app_history_group_end(AppHistory *);
void app_history_group_abort(AppHistory *, void *document);

#endif
