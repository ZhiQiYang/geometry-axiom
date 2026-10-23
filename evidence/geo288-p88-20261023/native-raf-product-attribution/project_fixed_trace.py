"""Read and project the already-completed fixed trace; no browser execution."""
from pathlib import Path
import collections
import hashlib
import json

BASE=Path(__file__).resolve().parent
SOURCE=Path('/tmp/g288p88r/fixed/trace.json')
raw=SOURCE.read_bytes(); d=json.loads(raw)


def slim(value):
    if isinstance(value,dict):
        return {key:({'sha256':hashlib.sha256(item.encode()).hexdigest(),'characters':len(item)}
                     if key in ('original_response_json','returned_response_json') else slim(item))
                for key,item in value.items()}
    if isinstance(value,list):
        return [slim(item) for item in value]
    if isinstance(value,str) and len(value)>700:
        return value[:700]+' [TRUNCATED IN DERIVED PROJECTION ONLY]'
    return value


events=d['events']; native=next(i for i,event in enumerate(events) if event['kind']=='native-restore-entry')
control=next(i for i,event in enumerate(events) if event['kind']=='controlled-native-raf-measurement')
start=max(i for i,event in enumerate(events[:native]) if event['kind']=='renderFaceInspector-enter')
following=[]
for event in events[control+1:]:
    if event['kind'] in ('measure','dom-pointerdown','dom-pointerup','dom-mousedown','dom-mouseup','dom-click','dom-focusin','dom-focusout','dom-scroll','renderFaceInspector-enter','renderFaceInspector-return'):
        following.append(slim(event))
        if len(following)==28:break
node_measure=next(i for i,event in enumerate(d['node_events']) if event['kind']=='measure-return' and str(event.get('measurement_id',event.get('id',''))) == str(d['injection']['measurement_id'])) if any(event['kind']=='measure-return' and str(event.get('measurement_id',event.get('id',''))) == str(d['injection']['measurement_id']) for event in d['node_events']) else None
projection={'scope':'Derived bounded projection of original completed fixed trace; not a new execution',
            'original_trace':{'path':str(SOURCE),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},
            'metadata':{key:d.get(key) for key in ('schema','mode','source_repo','source_sha256','app_source_sha256','restore_raf_line','restore_callback_sha256','requested_budgets_changed','original_return_values_preserved','target_invocations','completed','source_bytes_unchanged','errors')},
            'injection':slim(d['injection']),
            'event_kind_counts':dict(collections.Counter(event['kind'] for event in events)),
            'native_control_window':slim(events[start:control+1]),
            'first_following_events':following,
            'node_event_first_fields':{kind:list(next(event for event in d['node_events'] if event['kind']==kind)) for kind in ('measure-request','measure-return','cdp-mouse-request','cdp-mouse-ack')},
            'websocket_observation':d['websocket_observation']}
active=None; completed=0; nested=[]; orphan_up=[]; overlaps=[]
for event in events:
    if event['kind']=='dom-pointerdown' and event.get('phase')=='capture' and event.get('trusted'):
        if active:nested.append([active['down']['serial'],event['serial']])
        active={'down':event,'during':[]}
    elif event['kind']=='dom-pointerup' and event.get('phase')=='capture' and event.get('trusted'):
        if active:
            completed+=1
            if active['during']:
                overlaps.append(slim({'down':active['down'],'during':active['during'],'up':event}))
            active=None
        else:orphan_up.append(event['serial'])
    elif active and event['kind'] in ('renderFaceInspector-enter','renderFaceInspector-return','native-restore-entry','native-restore-return'):
        active['during'].append(event)
projection['recorded_pointer_interval_scan']={'scope':'Trusted recorded pointerdown-to-next-pointerup only; pointercancel was not observed by this tool',
    'completed_intervals':completed,'nested_down_serials':nested,'orphan_up_serials':orphan_up,
    'unclosed_down':None if not active else active['down']['serial'],'render_or_targeted_native_restore_overlaps':overlaps}
(BASE/'FIXED_TRACE_PROJECTION.json').write_text(json.dumps(projection,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'original_trace':projection['original_trace'],'metadata':projection['metadata'],
                  'native_control_window_rows':len(projection['native_control_window']),
                  'first_following_events':[{key:event.get(key) for key in ('serial','kind','epoch_ms','monotonic_ms','selector','type','target','x','y','clientX','clientY')} for event in following],
                  'node_event_first_fields':projection['node_event_first_fields']},ensure_ascii=False))
print(json.dumps({'recorded_pointer_interval_scan':{key:value for key,value in projection['recorded_pointer_interval_scan'].items() if key!='render_or_targeted_native_restore_overlaps'},
                  'overlap_count':len(overlaps),'overlap_rows':[{'down':row['down']['serial'],'down_target':row['down'].get('target'),
                      'during':[(item['serial'],item['kind'],item.get('invocation')) for item in row['during']],
                      'up':row['up']['serial'],'up_target':row['up'].get('target')} for row in overlaps]},ensure_ascii=False))
