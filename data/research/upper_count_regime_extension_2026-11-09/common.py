"""Small I/O and storage helpers; no model work at import."""
import hashlib,json,shutil
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from cases import HERE,ROOT

def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def stamp():return datetime.now(ZoneInfo('Australia/Perth')).isoformat()
def write(path,value):
    path=Path(path);temp=path.with_name(path.name+'.tmp')
    temp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');temp.replace(path)
def reserve(path):
    target=Path(path)
    while not target.exists():target=target.parent
    if shutil.disk_usage(ROOT).free<1073741824:raise RuntimeError('Preserve1GiB root filesystem reserve')
    if shutil.disk_usage(target).free<2147483648:raise RuntimeError('Preserve2GiB output filesystem reserve')
def require_unoptimized():
    if not __debug__:raise RuntimeError('Scientific audit assertions require unoptimized Python')
def validate_seal(folder):
    folder=Path(folder);seal=read(folder/'completion.json')
    if seal.get('status')!='complete':raise RuntimeError('Incomplete case seal')
    for name,digest in seal['files'].items():
        path=(folder/name).resolve()
        if path.parent!=folder.resolve() or sha(path)!=digest:raise RuntimeError('Case sealed bytes changed')
    return seal
