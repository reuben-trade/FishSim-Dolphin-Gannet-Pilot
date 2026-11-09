"""Source/input freezing only; this tool does not authorize native work."""
import argparse
from common import HERE,read,sha,write,stamp
from evidence import base_sources,verify_input_freeze

def create(stage):
    if stage=='inputs':
        pure=read(HERE/'PURE_PREFLIGHT.json')
        if pure.get('status')!='passed' or pure['native_steps'] or pure['native_constructions']:
            raise RuntimeError('Native-free preflight must pass')
        name='INPUT_FREEZE.json';result=dict(status='frozen_before_actual_initialization',at=stamp(),
            source_sha256=base_sources(),pure_preflight_sha256=sha(HERE/'PURE_PREFLIGHT.json'),native_steps=0)
    elif stage=='execution':
        inputs=verify_input_freeze();zero=read(HERE/'ACTUAL_ZERO_STEP.json')
        if (zero.get('status')!='passed' or zero.get('actual_cases')!=32 or zero.get('native_steps')!=0
                or zero.get('input_freeze_sha256')!=sha(HERE/'INPUT_FREEZE.json')):
            raise RuntimeError('All32 actual zero-step starts required')
        name='frozen_sources.json';sources=dict(inputs['source_sha256'])
        for filename in ('INPUT_FREEZE.json','PURE_PREFLIGHT.json','ACTUAL_ZERO_STEP.json'):
            sources[str((HERE/filename).resolve())]=sha(HERE/filename)
        result=dict(status='frozen_before_scientific_steps',at=stamp(),source_sha256=sources,
            input_freeze_sha256=sha(HERE/'INPUT_FREEZE.json'),actual_zero_step_sha256=sha(HERE/'ACTUAL_ZERO_STEP.json'),native_steps=0)
    else:raise ValueError('Unknown stage')
    if (HERE/name).exists():raise RuntimeError('Never overwrite a source freeze')
    write(HERE/name,result);return name

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=('inputs','execution'),required=True)
    print(create(parser.parse_args().stage))
