"""QA-only Python startup audit guard; no model or scientific code is changed.

Loaded through the exact inherited PYTHONPATH in the kernel and normal -B
model children. Python -I renderer children are explicitly outside this scope.
"""
import hashlib,json,os,sys,threading,time
from pathlib import Path

_CONFIG_ENV='FISHSIM_LOCAL_QA_GUARD_CONFIG'
_SOURCE_ENV='FISHSIM_LOCAL_QA_GUARD_SHA256'
_CONFIG_SHA_ENV='FISHSIM_LOCAL_QA_GUARD_CONFIG_SHA256'

def _fatal(message):
    os.write(2,('QA startup guard CLOSED: '+message+'\n').encode());os._exit(86)

if _CONFIG_ENV not in os.environ:_fatal('No actual source-bound QA guard configuration')
_config_path=Path(os.environ[_CONFIG_ENV]).resolve()
try:
    _raw=_config_path.read_bytes();_source=Path(__file__).read_bytes()
    if hashlib.sha256(_raw).hexdigest()!=os.environ.get(_CONFIG_SHA_ENV):_fatal('Config hash differs')
    if hashlib.sha256(_source).hexdigest()!=os.environ.get(_SOURCE_ENV):_fatal('Guard source hash differs')
    _config=json.loads(_raw)
    if _config.get('schema')!='professor_local_qa_guard_v1' or _config.get('enabled')is not True:_fatal('Guard is not activated')
    _denied=tuple(Path(p).resolve()for p in _config['deny_author_roots'])
    _dependencies=tuple(Path(p).resolve()for p in _config['allow_dependency_roots'])
    _logdir=Path(_config['audit_directory']).resolve()
    if not _logdir.is_dir():_fatal('Audit directory must already exist')
    _probe=Path(_config['blocked_probe_path']).resolve()
except BaseException as _error:_fatal(type(_error).__name__+': '+str(_error))

_tls=threading.local();_logfile=_logdir/(str(os.getpid())+'.jsonl');_probe_active=False

def _log(event,**fields):
    previous=getattr(_tls,'busy',False);_tls.busy=True
    try:
        payload=json.dumps(dict(event=event,pid=os.getpid(),ppid=os.getppid(),monotonic=time.monotonic(),**fields),sort_keys=True,allow_nan=False)+'\n'
        descriptor=os.open(_logfile,os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
        try:os.write(descriptor,payload.encode())
        finally:os.close(descriptor)
    finally:_tls.busy=previous

def _path(value):
    if isinstance(value,int)or not isinstance(value,(str,bytes,os.PathLike)):return None
    return Path(os.fsdecode(value)).resolve()

def _forbidden(path):
    if path is None:return False
    if any(path==base or path.is_relative_to(base)for base in _dependencies):return False
    return any(path==base or path.is_relative_to(base)for base in _denied)

def _audit(event,args):
    if getattr(_tls,'busy',False):return
    if event in ('open','os.listdir','os.scandir')and args:
        target=_path(args[0])
        if _forbidden(target):
            _log('denied_author_read',audit_event=event,path=str(target),expected_probe=bool(_probe_active and target==_probe))
            raise PermissionError('QA forbids original author study/source reads: '+str(target))
    elif event=='subprocess.Popen':
        _log('python_child_request',executable=str(args[0]),argv=args[1])
    elif event=='import'and args and(args[0]=='fish_sim'or args[0].startswith('fish_sim.')or args[0]=='cmodel'):
        filename=_path(args[1])if len(args)>1 and args[1]else None
        if _forbidden(filename):
            _log('denied_model_import',module=args[0],path=str(filename));raise PermissionError('QA forbids original author model import')
        _log('model_import',module=args[0],path=str(filename)if filename else None)

sys.addaudithook(_audit)
# Dependency view only: retain analysis NumPy/Matplotlib at their existing
# precedence, append the reviewed model environment for missing scientific deps.
for _directory in _config['append_dependency_sites']:
    _site=Path(_directory).resolve()
    if not any(_site==base or _site.is_relative_to(base)for base in _dependencies):_fatal('Appended dependency site must be explicitly allowlisted')
    if str(_site)not in sys.path:sys.path.append(str(_site))

_LOGGED_STARTUP=True
_log('guard_loaded',guard_sha256=hashlib.sha256(_source).hexdigest(),config_sha256=hashlib.sha256(_raw).hexdigest(),executable=sys.executable,argv=sys.argv,isolated=sys.flags.isolated,optimize=sys.flags.optimize,role='Python startup; model role is reconciled with source argv/import records')

def blocked_read_probe():
    """One intentional premodel denial in the kernel, no model construction."""
    global _probe_active
    _probe_active=True
    try:
        try:
            with _probe.open('rb')as handle:handle.read(1)
        except PermissionError:
            _log('blocked_probe_passed',path=str(_probe));return True
        raise RuntimeError('Forbidden original source probe unexpectedly succeeded')
    finally:_probe_active=False
