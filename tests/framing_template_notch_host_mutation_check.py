"""R03B named host withdrawals; reuse the exact 0/1/0 runner and byte restore.

These are Node protocol/history/ZIP gates. They do not claim native geometry
or true Chrome evidence. Each target remains in the existing Session owner.
"""
from pathlib import Path
import framing_template_host_mutation_check as host

host.JUDGE = Path(__file__).with_name('test_framing_template_notch_session.js')
host.FAULTS = [
    ('R03B_HOST_SKIP_L_SHAPE_GUARD', 'R03B_READ_SHAPE_BOUND',
     'version===3?notchOuter(r.source.outer,allowUnsupported):', 'version===3?true:'),
    ('R03B_HOST_SCOPE_REPORTED_AS_CONTRACT', 'R03B_READ_SCOPE_REASON',
     "if(this.template.version===3&&this.validateRead(r,true))throw fail('UNSUPPORTED_SCOPE'",
     "if(false)throw fail('UNSUPPORTED_SCOPE'"),
    ('R03B_HOST_SCOPE_BYPASSES_CONTRACT', 'R03B_READ_DAMAGED_CONTRACT',
     'this.template.version===3&&this.validateRead(r,true)', 'this.template.version===3'),
    ('R03B_HOST_DOWNGRADE_READ', 'R03B_READ_EXACT_VERSION',
     "schema:'framing-template-read/'+this.template.version,", "schema:'framing-template-read/2',"),
    ('R03B_HOST_SKIP_CANDIDATE_PIN', 'R03B_PREVIEW_PIN',
     "(this.template.version===1||same(p.template,this.currentRecipe?.template)&&hash(p.definitionFingerprint))",
     'true'),
    ('R03B_HOST_SKIP_ROLE_PRIORITY', 'R03B_PREVIEW_PIN',
     '(this.template.version!==3||notchRole(m))', 'true'),
    ('R03B_HOST_CANCEL_WRITES', 'R03B_CANCEL_ZERO_WRITE',
     'const command=`framing-template-cancel ${this.candidate.token} ${this.ownerKey}`;',
     'const command=`framing-template-confirm ${this.candidate.token} ${this.ownerKey}`;'),
    ('R03B_HOST_COLD_OPEN_SEARCH', 'R03B_COLD_RESTORE_NO_SEARCH',
     'this.collection=clone(value); // FT_H11_COLD_OPEN_NO_SEARCH: restoration has no native request.',
     "this.collection=clone(value); this.transport.post('/framing-template/preview',{schema:'framing-template-generate/1'});"),
]

if __name__ == '__main__':
    raise SystemExit(host.main())
