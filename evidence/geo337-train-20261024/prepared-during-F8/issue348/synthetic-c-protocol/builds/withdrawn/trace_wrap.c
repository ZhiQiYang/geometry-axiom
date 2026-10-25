/*
 * GEO348 command-boundary observer -- UNCOMPILED DIAGNOSTIC DRAFT.
 *
 * Link a separate TU with --wrap=fgets and --wrap=fflush. This draft has not
 * been calibrated against a product ELF. A later review must check actual
 * main-loop callsites, fortify/builtin bypass, exact source/ELF/input hashes,
 * and preservation of the original one-batch timeout and raw streams.
 *
 * Scope: one thread, one process, Linux, four known stdin protocol lines.
 * No product source changes, stdout markers, extra flushes, or EOF retries.
 * The parent opens dedicated ordinary files and passes both descriptors:
 *   GEO348_DIAG_EVENT_FD  : writable, initially empty JSONL file
 *   GEO348_DIAG_STATUS_FD : read/write, exactly 64 bytes, native uint64_t[8]
 * Status words: magic, version, attached, attempts, successes, faults, 0, 0.
 * Parent writes magic/version and zeroes every other word before execution.
 * Parent examines the mapping/file only after the original child is reaped.
 * An unattached status, fault, incomplete event, or counter mismatch makes
 * the diagnostic inconclusive; none is a product root-cause verdict.
 */
#define _POSIX_C_SOURCE 200809L

#if !defined(__linux__)
#error "GEO348 diagnostic draft supports Linux only"
#endif

#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

extern char *__real_fgets(char *restrict buffer, int size,
                          FILE *restrict stream);
extern int __real_fflush(FILE *stream);

enum {
    TRACE_MAGIC = 0,
    TRACE_VERSION = 1,
    TRACE_ATTACHED = 2,
    TRACE_ATTEMPTS = 3,
    TRACE_SUCCESSES = 4,
    TRACE_FAULTS = 5,
    TRACE_RESERVED_0 = 6,
    TRACE_RESERVED_1 = 7,
    TRACE_WORDS = 8,
    TRACE_STATUS_BYTES = 64
};

#define TRACE_MAGIC_VALUE UINT64_C(0x3334384449414731)
#define TRACE_VERSION_VALUE UINT64_C(1)

_Static_assert(TRACE_WORDS * sizeof(uint64_t) == TRACE_STATUS_BYTES,
               "GEO348 status layout must be eight native 64-bit words");

static int trace_initialization_attempted;
static int trace_event_fd = -1;
static volatile uint64_t *trace_status;
static uint64_t trace_command;

/* Strict digits only: no whitespace, signs, trailing bytes, or stdio FDs. */
static int trace_parse_fd(const char *name, int *out)
{
    const char *value = getenv(name);
    unsigned int number = 0;
    if (value == NULL || *value == '\0') return 0;
    for (const unsigned char *p = (const unsigned char *)value; *p; ++p) {
        unsigned int digit;
        if (*p < '0' || *p > '9') return 0;
        digit = (unsigned int)(*p - '0');
        if (number > ((unsigned int)INT_MAX - digit) / 10U) return 0;
        number = number * 10U + digit;
    }
    if (number <= 2U) return 0;
    *out = (int)number;
    return 1;
}

/*
 * Setup runs once before the first observed real function. On any setup
 * failure, leave attached=0 and still execute that real function normally.
 * No fopen, fdopen, stdio output, close, or product-stream flag changes.
 * Callers restore entry errno before invoking their real libc function.
 */
static void trace_initialize(void)
{
    int event_fd, status_fd, event_flags, status_flags;
    struct stat event_stat, status_stat;
    void *mapping;
    volatile uint64_t *words;

    if (trace_initialization_attempted) return;
    trace_initialization_attempted = 1;
    if (!trace_parse_fd("GEO348_DIAG_EVENT_FD", &event_fd) ||
        !trace_parse_fd("GEO348_DIAG_STATUS_FD", &status_fd) ||
        event_fd == status_fd) return;
    if (fstat(event_fd, &event_stat) != 0 ||
        fstat(status_fd, &status_stat) != 0 ||
        !S_ISREG(event_stat.st_mode) || !S_ISREG(status_stat.st_mode) ||
        event_stat.st_size != 0 ||
        status_stat.st_size != TRACE_STATUS_BYTES ||
        (event_stat.st_dev == status_stat.st_dev &&
         event_stat.st_ino == status_stat.st_ino)) return;
    event_flags = fcntl(event_fd, F_GETFL);
    status_flags = fcntl(status_fd, F_GETFL);
    if (event_flags == -1 || status_flags == -1 ||
        (event_flags & O_ACCMODE) == O_RDONLY ||
        (status_flags & O_ACCMODE) != O_RDWR) return;
    /* Empty file plus zero offset prevents a stale inherited offset hole. */
    if (lseek(event_fd, 0, SEEK_CUR) != 0) return;
    mapping = mmap(NULL, TRACE_STATUS_BYTES, PROT_READ | PROT_WRITE,
                   MAP_SHARED, status_fd, 0);
    if (mapping == MAP_FAILED) return;
    words = (volatile uint64_t *)mapping;
    if (words[TRACE_MAGIC] != TRACE_MAGIC_VALUE ||
        words[TRACE_VERSION] != TRACE_VERSION_VALUE ||
        words[TRACE_ATTACHED] != 0 || words[TRACE_ATTEMPTS] != 0 ||
        words[TRACE_SUCCESSES] != 0 || words[TRACE_FAULTS] != 0 ||
        words[TRACE_RESERVED_0] != 0 || words[TRACE_RESERVED_1] != 0) {
        (void)munmap(mapping, TRACE_STATUS_BYTES);
        return;
    }
    trace_event_fd = event_fd;
    trace_status = words;
    trace_status[TRACE_ATTACHED] = 1;
}

/* Direct regular-file writes survive child timeout/kill without stdio exit. */
static void trace_emit(const char *kind, int rc, uint64_t length,
                       int eof_flag, int error_flag)
{
    struct timespec now;
    uint64_t sequence, monotonic_ns, seconds;
    char line[384];
    int length_written;
    size_t offset;

    if (trace_status == NULL) return;
    sequence = trace_status[TRACE_ATTEMPTS] + 1;
    trace_status[TRACE_ATTEMPTS] = sequence;
    if (clock_gettime(CLOCK_MONOTONIC, &now) != 0 || now.tv_sec < 0 ||
        now.tv_nsec < 0 || now.tv_nsec >= 1000000000L) {
        trace_status[TRACE_FAULTS] += 1;
        return;
    }
    seconds = (uint64_t)now.tv_sec;
    if (seconds > (UINT64_MAX - (uint64_t)now.tv_nsec) / UINT64_C(1000000000)) {
        trace_status[TRACE_FAULTS] += 1;
        return;
    }
    monotonic_ns = seconds * UINT64_C(1000000000) + (uint64_t)now.tv_nsec;
    length_written = snprintf(
        line, sizeof line,
        "{\"seq\":%" PRIu64 ",\"kind\":\"%s\",\"command\":%" PRIu64
        ",\"monotonic_ns\":%" PRIu64 ",\"rc\":%d,\"length\":%" PRIu64
        ",\"feof\":%d,\"ferror\":%d}\n",
        sequence, kind, trace_command, monotonic_ns, rc, length,
        eof_flag, error_flag);
    if (length_written < 0 || (size_t)length_written >= sizeof line) {
        trace_status[TRACE_FAULTS] += 1;
        return;
    }
    offset = 0;
    while (offset < (size_t)length_written) {
        ssize_t written = write(trace_event_fd, line + offset,
                                (size_t)length_written - offset);
        if (written <= 0) {
            /* Even EINTR is an observer fault; never hide a failed write. */
            trace_status[TRACE_FAULTS] += 1;
            return;
        }
        offset += (size_t)written;
    }
    /* A kill between the write and this increment is conservatively invalid. */
    trace_status[TRACE_SUCCESSES] += 1;
}

char *__wrap_fgets(char *restrict buffer, int size, FILE *restrict stream)
{
    char *result;
    int entry_errno, result_errno, eof_flag, error_flag;

    /* Scene/tmpfile reads receive exactly their original one libc call. */
    if (stream != stdin) return __real_fgets(buffer, size, stream);
    entry_errno = errno;
    trace_initialize();
    errno = entry_errno;
    result = __real_fgets(buffer, size, stream);
    result_errno = errno;
    eof_flag = feof(stream);
    error_flag = ferror(stream);
    if (result != NULL) {
        trace_command += 1;
        trace_emit("stdin_line_returned", 1, (uint64_t)strlen(result),
                   eof_flag, error_flag);
    } else {
        /* A read error or unexplained NULL must never be called normal EOF. */
        trace_emit(eof_flag != 0 && error_flag == 0 ? "stdin_eof" : "stdin_error",
                   0, 0, eof_flag, error_flag);
    }
    errno = result_errno;
    return result;
}

int __wrap_fflush(FILE *stream)
{
    int entry_errno, result_errno, result, eof_flag, error_flag;

    /* fflush(NULL), scene and tmpfile flushes are not command boundaries. */
    if (stream != stdout) return __real_fflush(stream);
    entry_errno = errno;
    trace_initialize();
    eof_flag = feof(stream);
    error_flag = ferror(stream);
    trace_emit("stdout_flush_enter", 0, 0, eof_flag, error_flag);
    errno = entry_errno;
    result = __real_fflush(stream);
    result_errno = errno;
    eof_flag = feof(stream);
    error_flag = ferror(stream);
    /* PROTOCOL-ONLY NEGATIVE CONTROL: omit flush-return event. */
    errno = result_errno;
    return result;
}
