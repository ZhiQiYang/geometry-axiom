#include "history.h"
#include <string.h>

void app_history_init(AppHistory *history, size_t snapshot_size, size_t capacity,
    void *undo, void *redo, void *evicted, void *group_base)
{
    *history = (AppHistory){0};
    history->snapshot_size = snapshot_size;
    history->capacity = capacity;
    history->undo = undo;
    history->redo = redo;
    history->evicted = evicted;
    history->group_base = group_base;
}

void app_history_record(AppHistory *history, const void *document)
{
    history->record_redo_count = history->redo_count;
    history->record_evicted = history->undo_count >= history->capacity;
    if (history->record_evicted) {
        memcpy(history->evicted, history->undo, history->snapshot_size);
        memmove(history->undo, history->undo + history->snapshot_size,
            history->snapshot_size * (history->capacity - 1));
        --history->undo_count;
    }
    memcpy(history->undo + history->snapshot_size * history->undo_count++, document, history->snapshot_size);
    history->redo_count = 0;
}

void app_history_unrecord(AppHistory *history)
{
    if (history->undo_count > 0) --history->undo_count;
    if (history->record_evicted) {
        memmove(history->undo + history->snapshot_size, history->undo,
            history->snapshot_size * history->undo_count);
        memcpy(history->undo, history->evicted, history->snapshot_size);
        ++history->undo_count;
    }
    history->redo_count = history->record_redo_count;
    history->record_evicted = false;
}

void app_history_clear(AppHistory *history)
{
    history->undo_count = 0;
    history->redo_count = 0;
    history->grouping = false;
    history->group_dirty = false;
}

const void *app_history_peek_undo(const AppHistory *history)
{
    if (!history->undo_count) return NULL;
    return history->undo + history->snapshot_size * (history->undo_count - 1);
}

bool app_history_undo(AppHistory *history, void *document, AppHistoryRestore restore, void *opaque)
{
    if (history->undo_count == 0) return false;
    if (history->redo_count >= history->capacity) {
        memmove(history->redo, history->redo + history->snapshot_size,
            history->snapshot_size * (history->capacity - 1));
        --history->redo_count;
    }
    memcpy(history->redo + history->snapshot_size * history->redo_count++, document, history->snapshot_size);
    restore(document, history->undo + history->snapshot_size * --history->undo_count, opaque);
    return true;
}

bool app_history_redo(AppHistory *history, void *document, AppHistoryRestore restore, void *opaque)
{
    if (history->redo_count == 0) return false;
    if (history->undo_count >= history->capacity) {
        memmove(history->undo, history->undo + history->snapshot_size,
            history->snapshot_size * (history->capacity - 1));
        --history->undo_count;
    }
    memcpy(history->undo + history->snapshot_size * history->undo_count++, document, history->snapshot_size);
    restore(document, history->redo + history->snapshot_size * --history->redo_count, opaque);
    return true;
}

bool app_history_group_begin(AppHistory *history, const void *document)
{
    if (history->grouping) return false;
    memcpy(history->group_base, document, history->snapshot_size);
    history->grouping = true;
    history->group_dirty = false;
    return true;
}

void app_history_group_mark_dirty(AppHistory *history)
{
    if (history->grouping) history->group_dirty = true;
}

bool app_history_group_end(AppHistory *history)
{
    if (!history->grouping) return false;
    history->grouping = false;
    if (history->group_dirty) app_history_record(history, history->group_base);
    history->group_dirty = false;
    return true;
}

void app_history_group_abort(AppHistory *history, void *document)
{
    if (!history->grouping) return;
    memcpy(document, history->group_base, history->snapshot_size);
    history->grouping = false;
    history->group_dirty = false;
}
