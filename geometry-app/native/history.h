#ifndef GEO_APP_HISTORY_H
#define GEO_APP_HISTORY_H

#include <stdbool.h>
#include <stddef.h>

/* H owns whole-document snapshots. The buffers belong to the caller, must
 * remain alive, and must not overlap each other or the current document.
 * snapshot_size and capacity are positive; each stack has capacity complete
 * snapshots, and each backup has one. Initialization is a trusted host step.
 * No allocation, geometry, template policy, revision or presentation rules
 * live here. The product keeps its existing 32-entry static World buffers. */
typedef struct {
    size_t snapshot_size, capacity;
    unsigned char *undo, *redo, *evicted, *group_base;
    size_t undo_count, redo_count, record_redo_count;
    bool record_evicted, grouping, group_dirty;
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
