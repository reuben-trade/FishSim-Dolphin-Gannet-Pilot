"""Durable bounded supervisor with resource heartbeat and no automatic retries."""
import argparse,os,signal,subprocess,sys,time
from pathlib import Path
from common import HERE,read,sha,write,stamp,reserve
from cases import BULK,phase_output,phase_record,phase_cases
from evidence import require_approval

def resources(pid):
    result=dict(pid=pid)
    try:
        for line in (Path('/proc')/str(pid)/'status').read_text().splitlines():
            if line.startswith(('VmRSS:','VmHWM:','Threads:')):
                key,value=line.split(':',1);result[key]=value.strip()
        fields=(Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()
        result.update(user_cpu_ticks=int(fields[11]),system_cpu_ticks=int(fields[12]))
    except (OSError,ValueError,IndexError):pass
    return result

def live_group(pgid):
    found=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            v=(p/'stat').read_text().rsplit(')',1)[1].split()
            if int(v[2])==pgid and v[0] not in ('Z','X'):found.append(int(p.name))
        except (OSError,ValueError,IndexError):pass
    return found

def stop(process):
    try:os.killpg(process.pid,signal.SIGTERM)
    except ProcessLookupError:pass
    try:process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        process.wait()
    while live_group(process.pid):
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        time.sleep(.1)

def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=('smoke','pilot','remainder'),required=True);a=p.parse_args()
    require_approval(a.stage);BULK.mkdir(exist_ok=True)
    record_path=BULK/(a.stage+'_supervisor_v1.json');logpath=BULK/(a.stage+'_supervisor_v1.log')
    if record_path.exists() or logpath.exists():raise RuntimeError('Preserve previous attempts; no automatic retries')
    output=phase_output(a.stage)
    commands=[('native',[sys.executable,'-B',str(HERE/'run.py'),'--'+a.stage,'--workers','8']),
        ('physical',[sys.executable,'-B',str(HERE/'review_phase.py'),'--stage',a.stage])]
    if a.stage=='pilot':commands.append(('description',[sys.executable,'-B',str(HERE/'describe_pilot.py')]))
    if a.stage=='remainder':commands.append(('analysis',[sys.executable,'-B',str(HERE/'analyze.py')]))
    record=dict(status='running',stage=a.stage,at=stamp(),pid=os.getpid(),retries=0,
        protocol_sha256=sha(HERE/'protocol.json'),freeze_sha256=sha(HERE/'frozen_sources.json'),stages=[])
    write(record_path,record)
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env.pop('PYTHONOPTIMIZE',None)
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):env[key]='1'
    def interrupt(signum,frame):raise KeyboardInterrupt('Stop own child group before returning')
    signal.signal(signal.SIGTERM,interrupt)
    with logpath.open('x') as log:
        for label,command in commands:
            reserve(output);child=subprocess.Popen(command,cwd=HERE.parents[1],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            row=dict(stage=label,pid=child.pid,command=command,started_at=stamp());record['stages'].append(row);write(record_path,record)
            try:
                while child.poll() is None:
                    progress=[]
                    for case in phase_cases(a.stage):
                        path=output/'cases'/case.name/'progress.json'
                        try:
                            value=read(path);progress.append(dict(case=case.name,native_steps=value.get('native_steps',0),elapsed=value.get('elapsed',0),complete=(path.parent/'completion.json').exists(),resource=resources(value.get('pid',-1))))
                        except (OSError,ValueError):pass
                    available=next((line for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')),None)
                    write(BULK/(a.stage+'_heartbeat_v1.json'),dict(at=stamp(),stage=label,child_pid=child.pid,
                        complete=sum(v['complete'] for v in progress),cases=progress,host_mem_available=available))
                    try:child.wait(timeout=20)
                    except subprocess.TimeoutExpired:pass
            except BaseException:
                stop(child);record.update(status='failed_or_partial',finished_at=stamp(),failed_stage=label);write(record_path,record);raise
            row.update(finished_at=stamp(),exit_code=child.returncode);write(record_path,record)
            if child.returncode or live_group(child.pid):
                stop(child);record.update(status='failed_or_partial',finished_at=stamp(),failed_stage=label);write(record_path,record)
                raise SystemExit(child.returncode or 1)
    record.update(status='complete',finished_at=stamp(),output=str(output));write(record_path,record)
    print({k:v for k,v in record.items() if k!='stages'},flush=True)
if __name__=='__main__':main()
