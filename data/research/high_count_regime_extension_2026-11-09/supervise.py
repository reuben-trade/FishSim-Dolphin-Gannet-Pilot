"""Durable foreground process/heartbeat; approvals are supplied separately."""
import argparse,os,subprocess,sys
from common import HERE,read,sha,write,stamp,reserve
from cases import BULK
from evidence import require_approval

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=('smoke','full'),required=True);args=parser.parse_args()
    require_approval(args.stage);BULK.mkdir(exist_ok=True)
    record_path=BULK/(args.stage+'_supervisor_v1.json');logpath=BULK/(args.stage+'_supervisor_v1.log')
    if record_path.exists() or logpath.exists():raise RuntimeError('Fresh supervisor required; no retry')
    output=BULK/('smoke_4T_v1' if args.stage=='smoke' else 'full_36T_v1')
    commands=[('native',[sys.executable,str(HERE/'run.py'),'--smoke' if args.stage=='smoke' else '--execute','--workers','3']),
              ('physical',[sys.executable,str(HERE/'review_actual.py'),'--output',str(output)])]
    if args.stage=='full':commands.append(('analysis',[sys.executable,str(HERE/'analyze.py')]))
    record=dict(status='running',stage=args.stage,at=stamp(),pid=os.getpid(),retries=0,
        protocol_sha256=sha(HERE/'protocol.json'),freeze_sha256=sha(HERE/'frozen_sources.json'),stages=[])
    write(record_path,record)
    with logpath.open('x') as log:
        for label,command in commands:
            reserve(output);child=subprocess.Popen(command,cwd=HERE.parents[1],stdout=log,stderr=subprocess.STDOUT)
            row=dict(stage=label,pid=child.pid,command=command,started_at=stamp());record['stages'].append(row);write(record_path,record)
            while child.poll() is None:
                progress=[]
                for path in sorted((output/'cases').glob('*/progress.json')):
                    try:
                        value=read(path);progress.append(dict(case=path.parent.name,native_steps=value.get('native_steps',0),
                            elapsed=value.get('elapsed',0),complete=(path.parent/'completion.json').exists()))
                    except (OSError,ValueError):pass
                write(BULK/(args.stage+'_heartbeat_v1.json'),dict(at=stamp(),stage=label,child_pid=child.pid,
                    complete=sum(v['complete'] for v in progress),cases=progress))
                try:child.wait(timeout=20)
                except subprocess.TimeoutExpired:pass
            row.update(finished_at=stamp(),exit_code=child.returncode);write(record_path,record)
            if child.returncode:
                record.update(status='failed_or_partial',finished_at=stamp(),failed_stage=label);write(record_path,record)
                raise SystemExit(child.returncode)
    record.update(status='complete',finished_at=stamp(),output=str(output));write(record_path,record)
    print({k:v for k,v in record.items() if k!='stages'})

if __name__=='__main__':main()
