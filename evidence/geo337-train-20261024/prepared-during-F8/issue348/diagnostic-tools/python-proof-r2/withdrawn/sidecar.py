"""Read diagnostic observations, never a product acceptance verdict."""
import json, struct

MAGIC = 0x3334384449414731
STATUS = struct.Struct('=8Q')
TIMEOUT = 600

class InvalidObservation(ValueError):
    pass

def must(value, reason):
    if not value:
        raise InvalidObservation(reason)

def inspect_events(raw, status_raw, payload, *, completed=False):
    result = {'valid': False, 'errors': [], 'events': [], 'flushed_commands': [],
              'last_boundary': 'UNKNOWN', 'root_cause': None, 'product_gate_verdict': None}
    try:
        lines = payload.splitlines(keepends=True)
        must(len(lines) == 4 and all(x.endswith(b'\n') for x in lines), 'exact-four-input-lines')
        must(lines[0].startswith(b'loadfile ') and lines[1:] == [b'dump\n', b'objects\n', b'references\n'], 'original-command-order')
        must(len(status_raw) == STATUS.size, 'status-size')
        magic, version, attached, attempts, successes, faults, reserved0, reserved1 = STATUS.unpack(status_raw)
        result['status'] = dict(attached=attached, attempts=attempts, successes=successes, faults=faults)
        must((magic, version, attached, reserved0, reserved1) == (MAGIC, 1, 1, 0, 0), 'wrapper-attachment-or-status-identity')
        must(faults == 0 and attempts == successes, 'observer-write-or-clock-fault')
        must(not raw or raw.endswith(b'\n'), 'truncated-sidecar-event')
        events = [json.loads(line) for line in raw.splitlines()]
        must(len(events) == attempts, 'status-event-count')
        current, state, last_time, eof = 0, 'idle', 0, False
        fields = {'seq', 'kind', 'command', 'monotonic_ns', 'rc', 'length', 'feof', 'ferror'}
        for sequence, event in enumerate(events, 1):
            must(isinstance(event, dict) and set(event) == fields, 'event-fields')
            must(all(type(event[k]) is int for k in fields - {'kind'}), 'event-integer-fields')
            must(event['feof'] >= 0 and event['ferror'] >= 0 and event['length'] >= 0, 'negative-libc-flag-or-length')
            must(event['seq'] == sequence, 'event-sequence')
            must(event['monotonic_ns'] >= last_time and event['monotonic_ns'] > 0, 'monotonic-event-time')
            last_time = event['monotonic_ns']
            kind, command = event['kind'], event['command']
            must(not eof, 'event-after-input-terminal')
            if kind == 'stdin_line_returned':
                must(state == 'idle' and command == current + 1 and 1 <= command <= 4, 'input-command-identity')
                pass  # WITHDRAWAL_ANCHOR: deliberately omit original input line length check
                must(event['rc'] == 1 and event['feof'] == 0 and event['ferror'] == 0, 'input-return-flags')
                current, state = command, 'handler'
            elif kind == 'stdout_flush_enter':
                must(state == 'handler' and command == current, 'flush-entry-order')
                must(event['length'] == 0 and event['rc'] == 0, 'flush-entry-fields')
                state = 'flush'
            elif kind == 'stdout_flush_return':
                must(state == 'flush' and command == current, 'flush-return-order')
                must(event['length'] == 0 and event['rc'] in (0, -1), 'flush-return-fields')
                result['flushed_commands'].append({'command': command, 'rc': event['rc']})
                state = 'idle'
            elif kind in ('stdin_eof', 'stdin_error'):
                must(state == 'idle' and command == current and event['length'] == 0 and event['rc'] == 0, 'input-terminal-order')
                if kind == 'stdin_eof':
                    must(event['feof'] != 0 and event['ferror'] == 0, 'eof-must-not-be-read-error')
                else:
                    must(event['ferror'] != 0 or event['feof'] == 0, 'read-error-flags')
                eof = True
            else:
                raise InvalidObservation('unknown-event-kind')
            result['events'].append(event)
            result['last_boundary'] = {'kind': kind, 'command': command, 'monotonic_ns': last_time}
        if completed:
            must(current == 4 and len(result['flushed_commands']) == 4 and eof, 'normal-terminal-missing-boundary')
        result['valid'] = True
        result['scope'] = 'Handler/flush boundary observations only; JSON success and product acceptance remain separate.'
    except (InvalidObservation, ValueError, TypeError, struct.error, UnicodeError) as exc:
        result['errors'].append(str(exc))
    return result
