/* Protocol-only synthetic stub. No geometry/product code or performance work. */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

static int file_ok, file_errno, tmp_rc, tmp_errno, all_rc, all_errno;
static int bad_null, bad_errno, bad_eof, bad_error;
static int read_errno[5], flush_rc[4], flush_errno[4];

static int write_all(int fd, const char *data, size_t length)
{
    size_t done = 0;
    while (done < length) {
        ssize_t n = write(fd, data + done, length - done);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) return -1;
        done += (size_t)n;
    }
    return 0;
}

static int save_pid(void)
{
    const char *path = getenv("STUB_PID_PATH");
    char value[40];
    int fd, n, rc;
    if (!path) return -1;
    fd = open(path, O_WRONLY | O_CREAT | O_EXCL, 0600);
    if (fd < 0) return -1;
    n = snprintf(value, sizeof value, "%ld\n", (long)getpid());
    rc = write_all(fd, value, (size_t)n);
    if (close(fd) != 0) return -1;
    return rc;
}

static int nonmatching_controls(void)
{
    const char *fixture = getenv("STUB_FIXTURE");
    char buffer[64];
    char *got;
    FILE *file, *tmp, *bad;
    if (!fixture) return -1;
    file = fopen(fixture, "rb");
    if (!file) return -1;
    errno = EDOM;
    got = fgets(buffer, sizeof buffer, file);
    file_errno = errno;
    file_ok = got != NULL && strcmp(buffer, "protocol-only fixture\n") == 0;
    if (fclose(file) != 0) return -1;
    tmp = tmpfile();
    if (!tmp || fputs("temporary\n", tmp) == EOF) return -1;
    errno = ERANGE;
    tmp_rc = fflush(tmp);
    tmp_errno = errno;
    if (fclose(tmp) != 0) return -1;
    errno = EOVERFLOW;
    all_rc = fflush(NULL);
    all_errno = errno;
    bad = fopen(fixture, "rb");
    if (!bad || close(fileno(bad)) != 0) return -1;
    errno = EDOM;
    got = fgets(buffer, sizeof buffer, bad);
    bad_errno = errno;
    bad_null = got == NULL;
    bad_eof = feof(bad);
    bad_error = ferror(bad);
    (void)fclose(bad); /* Expected EBADF: no new descriptor opened meanwhile. */
    return 0;
}

static void report_metrics(int reads, int flushes, int eof_flag, int error_flag)
{
    char line[768];
    int n = snprintf(line, sizeof line,
        "CONTROL file_ok=%d file_errno=%d tmp_rc=%d tmp_errno=%d "
        "all_rc=%d all_errno=%d bad_null=%d bad_errno=%d bad_eof=%d bad_error=%d "
        "reads=%d read_errno=%d,%d,%d,%d,%d flushes=%d "
        "flush_rc=%d,%d,%d,%d flush_errno=%d,%d,%d,%d eof=%d error=%d\n",
        file_ok, file_errno, tmp_rc, tmp_errno, all_rc, all_errno,
        bad_null, bad_errno, bad_eof, bad_error, reads,
        read_errno[0], read_errno[1], read_errno[2], read_errno[3], read_errno[4],
        flushes, flush_rc[0], flush_rc[1], flush_rc[2], flush_rc[3],
        flush_errno[0], flush_errno[1], flush_errno[2], flush_errno[3],
        eof_flag, error_flag);
    if (n > 0 && (size_t)n < sizeof line) (void)write_all(STDERR_FILENO, line, (size_t)n);
}

int main(int argc, char **argv)
{
    const char *mode = argc == 2 ? argv[1] : "normal";
    char line[4096];
    int reads = 0, flushes = 0, command = 0, ended_eof = 0, ended_error = 0;
    if (save_pid() != 0 || nonmatching_controls() != 0) return 90;
    if (strcmp(mode, "stress") == 0) {
        char block[4096];
        memset(block, 'E', sizeof block);
        for (int i = 0; i < 64; ++i)
            if (write_all(STDERR_FILENO, block, sizeof block) != 0) return 91;
    }
    if (strcmp(mode, "stdin_error") == 0 && close(STDIN_FILENO) != 0) return 92;
    for (;;) {
        char *got;
        int saved_errno;
        errno = EBUSY;
        got = fgets(line, sizeof line, stdin);
        saved_errno = errno;
        if (reads < 5) read_errno[reads] = saved_errno;
        ++reads;
        if (!got) {
            ended_eof = feof(stdin);
            ended_error = ferror(stdin);
            break;
        }
        ++command;
        if (command > 4) return 93;
        if (strcmp(mode, "hang") == 0 && command == 2) {
            (void)write_all(STDOUT_FILENO, "{\"ok\":", 6);
            (void)write_all(STDERR_FILENO, "synthetic timeout partial stderr\n", 33);
            for (;;) pause();
        }
        if (strcmp(mode, "event_write_error") == 0 && command == 1) {
            const char *fd = getenv("GEO348_DIAG_EVENT_FD");
            if (!fd || close(atoi(fd)) != 0) return 94;
        }
        if (strcmp(mode, "stress") == 0) {
            char tail[80];
            struct timespec delay = {0, 10000000L};
            int n = snprintf(tail, sizeof tail, "true,\"command\":%d}\n", command);
            if (write_all(STDOUT_FILENO, "{\"ok\":", 6) != 0) return 95;
            (void)nanosleep(&delay, NULL);
            if (write_all(STDOUT_FILENO, tail, (size_t)n) != 0) return 96;
        } else {
            printf("{\"ok\":true,\"command\":%d}\n", command);
        }
        if (strcmp(mode, "stdout_error") == 0 && close(STDOUT_FILENO) != 0) return 97;
        errno = ERANGE;
        flush_rc[flushes] = fflush(stdout);
        flush_errno[flushes] = errno;
        ++flushes;
        if (strcmp(mode, "stdout_error") == 0) {
            report_metrics(reads, flushes, feof(stdout), ferror(stdout));
            return 24;
        }
    }
    report_metrics(reads, flushes, ended_eof, ended_error);
    return ended_error ? 23 : 0;
}
