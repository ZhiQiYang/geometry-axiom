#include "history.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* H382: a shifting-list oracle, independent of the product's physical slots.
 * Only history.c is built with the counted memcpy/memmove names. */
static size_t copied_bytes, copy_calls;
void *h382_counted_memcpy(void *dst, const void *src, size_t size)
{ copied_bytes += size; ++copy_calls; return memcpy(dst, src, size); }
void *h382_counted_memmove(void *dst, const void *src, size_t size)
{ copied_bytes += size; ++copy_calls; return memmove(dst, src, size); }

#define LIMIT 32
typedef struct { unsigned char bytes[64]; } Value;
typedef struct {
    Value undo[LIMIT], redo[LIMIT], evicted, group;
    AppHistory history;
} Storage;
typedef struct {
    Value undo[LIMIT], redo[LIMIT], group;
    size_t undo_count, redo_count, capacity;
    int grouping, dirty;
} Oracle;
typedef struct { unsigned calls; int preserve; } Restore;
static unsigned steps;

#define CHECK(c, name) do { if (!(c)) { \
    fprintf(stderr, "ASSERT:%s step=%u\n", name, steps); return 1; \
} } while (0)

static Value value(unsigned id)
{
    Value v;
    uint32_t state = id + UINT32_C(0x9e3779b9);
    for (size_t i = 0; i < sizeof v; ++i) {
        state = state * UINT32_C(1664525) + UINT32_C(1013904223);
        v.bytes[i] = (unsigned char)(state >> 24);
    }
    return v;
}
static void restore(void *document, const void *snapshot, void *opaque)
{
    Restore *r = opaque;
    Value saved = *(Value *)document;
    memcpy(document, snapshot, sizeof(Value));
    if (r->preserve) memcpy(((Value *)document)->bytes + 48, saved.bytes + 48, 16);
    ++r->calls;
}
static void oracle_push(Value *stack, size_t *count, size_t capacity, Value v)
{
    if (*count == capacity) {
        for (size_t i = 1; i < *count; ++i) stack[i - 1] = stack[i];
        --*count;
    }
    stack[(*count)++] = v;
}
static void oracle_record(Oracle *o, Value v)
{ oracle_push(o->undo, &o->undo_count, o->capacity, v); o->redo_count = 0; }
static int verify(const Storage *s, const Oracle *o, const Value *actual, const Value *expected)
{
    CHECK(!memcmp(actual, expected, sizeof *actual), "H382_DOCUMENT_BYTES");
    CHECK(s->history.undo_count == o->undo_count && s->history.redo_count == o->redo_count,
          "H382_HISTORY_COUNTS");
    CHECK(s->history.undo_count + s->history.redo_count <= o->capacity, "H382_LOGICAL_CAPACITY");
    CHECK(s->history.grouping == !!o->grouping && s->history.group_dirty == !!o->dirty,
          "H382_GROUP_FLAGS");
    const void *peek = app_history_peek_undo(&s->history);
    CHECK(o->undo_count ? peek != NULL : peek == NULL, "H382_PEEK_PRESENCE");
    if (peek) CHECK(!memcmp(peek, &o->undo[o->undo_count - 1], sizeof(Value)), "H382_LOGICAL_BYTES");
    /* Unused caller-owned array tails are not extra logical/physical slots. */
    for (size_t i = o->capacity; i < LIMIT; ++i)
        for (size_t j = 0; j < sizeof(Value); ++j)
            CHECK(s->undo[i].bytes[j] == 0xa5 && s->redo[i].bytes[j] == 0xa5, "H382_STORAGE_BOUNDS");
    return 0;
}
static void init(Storage *s, Oracle *o, size_t capacity)
{
    memset(s, 0xa5, sizeof *s);
    memset(o, 0, sizeof *o); o->capacity = capacity;
    app_history_init(&s->history, sizeof(Value), capacity, s->undo, s->redo, &s->evicted, &s->group);
}
static int move(Storage *s, Oracle *o, Value *actual, Value *expected, Restore *r, int redo)
{
    size_t *from_count = redo ? &o->redo_count : &o->undo_count;
    size_t *to_count = redo ? &o->undo_count : &o->redo_count;
    Value *from = redo ? o->redo : o->undo, *to = redo ? o->undo : o->redo;
    unsigned before = r->calls;
    int present = *from_count != 0;
    int result = redo ? app_history_redo(&s->history, actual, restore, r)
                      : app_history_undo(&s->history, actual, restore, r);
    CHECK(result == present && r->calls == before + (unsigned)present, "H382_RESTORE_CALLS");
    if (present) {
        Value old = *expected;
        oracle_push(to, to_count, o->capacity, old);
        *expected = from[--*from_count];
        if (r->preserve) memcpy(expected->bytes + 48, old.bytes + 48, 16);
    }
    return verify(s, o, actual, expected);
}
static int rejected(Storage *s, Oracle *o, Value *actual, Value *expected)
{
    /* The host's failed-command path: record, restore peek, unrecord. */
    Oracle before = *o;
    app_history_record(&s->history, actual); oracle_record(o, *expected);
    *actual = value(1000000u + steps);
    CHECK(app_history_peek_undo(&s->history) != NULL, "H382_FAILURE_HAS_BEFORE");
    memcpy(actual, app_history_peek_undo(&s->history), sizeof *actual);
    app_history_unrecord(&s->history); *o = before;
    CHECK(!s->history.record_evicted, "H382_FAILURE_CLEARS_MARKER");
    return verify(s, o, actual, expected);
}
static int semantic_case(void)
{
    const size_t capacities[] = {1, 2, 3, 7, 32};
    for (size_t ci = 0; ci < sizeof capacities / sizeof capacities[0]; ++ci) {
        Storage s; Oracle o; init(&s, &o, capacities[ci]);
        Value actual = value(0), expected = actual; Restore r = {0};
        CHECK(!verify(&s, &o, &actual, &expected), "H382_INITIAL");
        /* More than three complete physical turns, rejecting at every head. */
        for (unsigned i = 1; i <= 3 * (capacities[ci] + 1) + 5; ++i) {
            ++steps; app_history_record(&s.history, &actual); oracle_record(&o, expected);
            actual = expected = value(i);
            CHECK(!verify(&s, &o, &actual, &expected), "H382_WRAP_RECORD");
            CHECK(!rejected(&s, &o, &actual, &expected), "H382_WRAP_REJECTION");
        }
        uint32_t random = 382;
        for (unsigned i = 0; i < 8000; ++i) {
            ++steps; random = random * UINT32_C(1664525) + UINT32_C(1013904223);
            unsigned op = (random >> 16) % 12;
            if (op < 4) {
                app_history_record(&s.history, &actual); oracle_record(&o, expected);
                actual = expected = value(steps);
            } else if (op < 7) {
                r.preserve = (random >> 28) & 1;
                CHECK(!move(&s, &o, &actual, &expected, &r, op == 6), "H382_MOVE");
            } else if (op == 7) {
                CHECK(!rejected(&s, &o, &actual, &expected), "H382_REJECTION");
            } else if (op < 11) {
                CHECK(app_history_group_begin(&s.history, &actual), "H382_GROUP_BEGIN");
                o.group = expected; o.grouping = 1;
                CHECK(!app_history_group_begin(&s.history, &actual), "H382_NESTED_GROUP_REJECTED");
                if (op != 8) {
                    actual = expected = value(steps);
                    app_history_group_mark_dirty(&s.history); o.dirty = 1;
                }
                if (op == 10) {
                    unsigned calls = r.calls;
                    app_history_group_abort(&s.history, &actual); expected = o.group;
                    o.grouping = o.dirty = 0;
                    app_history_group_abort(&s.history, &actual);
                    CHECK(r.calls == calls, "H382_ABORT_NOT_RESTORE_HOOK");
                } else {
                    CHECK(app_history_group_end(&s.history), "H382_GROUP_END");
                    if (o.dirty) oracle_record(&o, o.group);
                    o.grouping = o.dirty = 0;
                    CHECK(!app_history_group_end(&s.history), "H382_END_WITHOUT_GROUP");
                }
            } else if ((random & 255) == 0) {
                app_history_clear(&s.history); o.undo_count = o.redo_count = 0;
                o.grouping = o.dirty = 0;
            }
            CHECK(!verify(&s, &o, &actual, &expected), "H382_SEQUENCE");
        }
        r.preserve = 0;
        while (o.undo_count) CHECK(!move(&s, &o, &actual, &expected, &r, 0), "H382_DRAIN_UNDO");
        CHECK(!move(&s, &o, &actual, &expected, &r, 0), "H382_EMPTY_UNDO");
        while (o.redo_count) CHECK(!move(&s, &o, &actual, &expected, &r, 1), "H382_DRAIN_REDO");
        CHECK(!move(&s, &o, &actual, &expected, &r, 1), "H382_EMPTY_REDO");
        app_history_group_begin(&s.history, &actual); app_history_group_mark_dirty(&s.history);
        app_history_clear(&s.history); o.undo_count = o.redo_count = o.grouping = o.dirty = 0;
        CHECK(!verify(&s, &o, &actual, &expected), "H382_CLEAR_ACTIVE_GROUP");
        CHECK(!app_history_group_end(&s.history), "H382_CLEAR_CLOSED_GROUP");
    }
    printf("H382_CHARACTERIZATION steps=%u capacities=1,2,3,7,32 failures=0\n", steps);
    return 0;
}
static int cost_case(int rollback)
{
    Storage s; Oracle o; init(&s, &o, LIMIT); Value document = value(0);
    for (unsigned i = 0; i < LIMIT; ++i) app_history_record(&s.history, &document);
    for (unsigned i = 0; i < 4 * (LIMIT + 1); ++i) {
        ++steps; copied_bytes = copy_calls = 0;
        app_history_record(&s.history, &document);
        if (rollback) {
            copied_bytes = copy_calls = 0;
            app_history_unrecord(&s.history);
            if (!i) printf("H382_COST_OBSERVED unrecord bytes=%zu calls=%zu snapshot=%zu\n", copied_bytes, copy_calls, sizeof document);
            CHECK(copied_bytes == 0 && copy_calls == 0, "H382_FULL_UNRECORD_COPIES_ZERO");
            app_history_record(&s.history, &document);
        } else {
            if (!i) printf("H382_COST_OBSERVED record bytes=%zu calls=%zu snapshot=%zu\n", copied_bytes, copy_calls, sizeof document);
            CHECK(copied_bytes == sizeof document && copy_calls == 1, "H382_FULL_RECORD_COPIES_ONE");
        }
    }
    printf("H382_COST mode=%s steps=%u copied_bytes=%zu copy_calls=%zu snapshot_bytes=%zu\n",
           rollback ? "unrecord" : "record", steps, rollback ? (size_t)0 : sizeof document,
           rollback ? (size_t)0 : (size_t)1, sizeof document);
    return 0;
}
/* Uninstrumented builds use the very same client for paired timing. The time
 * below is process CPU time; allocation/warm-up are outside the sample. */
static int benchmark(size_t size, unsigned iterations, int mode)
{
    unsigned char *undo = malloc(LIMIT * size), *redo = malloc(LIMIT * size);
    unsigned char *evicted = malloc(size), *group = malloc(size), *document = malloc(size);
    if (!undo || !redo || !evicted || !group || !document) return 2;
    memset(undo, 0, LIMIT * size); memset(redo, 0, LIMIT * size);
    memset(evicted, 0, size); memset(group, 0, size); memset(document, 0x5a, size);
    AppHistory h; app_history_init(&h, size, LIMIT, undo, redo, evicted, group);
    for (unsigned i = 0; i < LIMIT + 33; ++i) app_history_record(&h, document);
    if (mode == 2) app_history_clear(&h);
    clock_t begin = clock();
    for (unsigned i = 0; i < iterations; ++i) {
        document[i % size] ^= (unsigned char)(i + 1);
        app_history_record(&h, document);
        if (mode == 1 || mode == 2) app_history_unrecord(&h);
    }
    clock_t elapsed = clock() - begin;
    const unsigned char *peek = app_history_peek_undo(&h);
    printf("{\"snapshot_bytes\":%zu,\"iterations\":%u,\"mode\":%d,\"cpu_seconds\":%.9f,\"checksum\":%u}\n",
        size, iterations, mode, (double)elapsed / CLOCKS_PER_SEC,
        peek ? (unsigned)peek[0] : 0u);
    free(undo); free(redo); free(evicted); free(group); free(document); return 0;
}
int main(int argc, char **argv)
{
    if (argc == 2 && !strcmp(argv[1], "semantic")) return semantic_case();
    if (argc == 2 && !strcmp(argv[1], "record-cost")) return cost_case(0);
    if (argc == 2 && !strcmp(argv[1], "rollback-cost")) return cost_case(1);
    if (argc == 5 && !strcmp(argv[1], "benchmark"))
        return benchmark((size_t)strtoull(argv[2], NULL, 10), (unsigned)strtoul(argv[3], NULL, 10), atoi(argv[4]));
    return 2;
}
