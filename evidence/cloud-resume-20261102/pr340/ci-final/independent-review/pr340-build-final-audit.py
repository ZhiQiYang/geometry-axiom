from pathlib import Path

OUT = Path(__file__).resolve().parent
source = (OUT / 'check_current_native_browser.py').read_text()
source = source.replace('20261102T033519Z','20261102T035010Z')
source = source.replace('independent-native-browser-check.json','pr340-final-native-browser-check.json')
strict = '''def strict_json(value):
    def unique(pairs):
        out = {}
        for key, item in pairs:
            if key in out:
                raise ValueError('duplicate raw marker JSON key: '+key)
            out[key] = item
        return out
    return json.loads(value, object_pairs_hook=unique)


'''
source = source.replace('def load(path):',strict+'def load(path):')
source = source.replace('json.loads(line)', 'strict_json(line)').replace('json.loads(line.split(" ", 1)[1])','strict_json(line.split(" ", 1)[1])')
extra = '''run = load(ROOT / 'api/20261102T035010Z/integration-run.json')
require(run['id'] == 41382015317 and run['head_sha'] == HEAD and run['run_attempt'] == 1
        and run['status'] == 'completed' and run['conclusion'] == 'success', 'official integration terminal success')
require(len(browser) == 6 and pending_browser == [], 'six completed browser groups, no pending')
require({row['name'] for row in browser} == {'browser ('+name+')' for name in ['assembly','documents','grid','space','timber','canvas']},
        'exact six current workflow browser names')
canvas = next(row for row in browser if row['name'] == 'browser (canvas)')
canvas_log_path = ROOT / 'job-logs' / (str(canvas['id'])+'.txt')
canvas_lines = canvas_log_path.read_text().splitlines()
result_index = next(index for index,line in enumerate(canvas_lines) if 'Z CDP_RESULT {' in line)
traceback_lines = [{'line':index+1,'text':line} for index,line in enumerate(canvas_lines) if 'BrokenPipeError:' in line or 'Exception occurred during processing of request' in line]
require(all(row['line'] > result_index+1 for row in traceback_lines), 'server request traceback is in workflow-appended server log after harness result')
require(sum('Exception occurred during processing of request' in row['text'] for row in traceback_lines) == 1
        and sum('BrokenPipeError:' in row['text'] for row in traceback_lines) == 2,
        'one chained server request BrokenPipe traceback retained explicitly')
canvas['server_log_diagnostics'] = dict(processing_request_exceptions=1, chained_broken_pipe_lines=2,
    lines=traceback_lines, phase='workflow appends server log after browser command; does not alter original browser process status',
    origin='serve.py /sources/snapshot response write; chained error-response write also meets the closed socket',
    classification='Recorded server request diagnostics, not an additional uncaught browser exception or failed controlled assertion; exact cause of client socket closure is not established by this log.')
(OUT / 'pr340-canvas-server-diagnostics.txt').write_text('\\n'.join(canvas_lines[result_index+1:][next(index for index,line in enumerate(canvas_lines[result_index+1:]) if 'Exception occurred during processing of request' in line)-1:])+'\\n')
canvas['raw_log_sha256'] = hashlib.sha256(canvas_log_path.read_bytes()).hexdigest()
canvas['current_golden_sha256'] = hashlib.sha256((SOURCE / 'geometry-web/cdp_sections.golden.json').read_bytes()).hexdigest()
canvas['current_harness_sha256'] = hashlib.sha256((SOURCE / 'geometry-web/cdp_test.js').read_bytes()).hexdigest()

'''
source = source.replace('report = dict(passed=True,',extra+'report = dict(passed=True, integration_run_id=run["id"], integration_conclusion=run["conclusion"], audit_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),')
(OUT / 'pr340-final-check-native-browser.py').write_text(source)
