"""Versioned native facade: prohibit saved-analysis headless launch contexts.

All release validation, argument planning and native execution remain delegated
to the byte-exact e37 helper. This layer only blocks the legacy analysis driver's
180-second/native-zero receipt context before any native workflow delegation.
"""
from __future__ import annotations
import os
from pathlib import Path
from . import optional_native as _base

validate_release=_base.validate_release
argument_plan=_base.argument_plan


def headless_markers(root,environ=None):
    root=Path(root).expanduser().resolve();environment=os.environ if environ is None else environ
    expected={'IPYTHONDIR':root/'.headless/ipython','JUPYTER_RUNTIME_DIR':root/'.headless/runtime','JUPYTER_PATH':root/'.headless/share/jupyter'}
    matched=[]
    for name,base in expected.items():
        value=environment.get(name,'')
        values=value.split(os.pathsep) if name=='JUPYTER_PATH' else [value]
        for part in values:
            if not part:continue
            path=Path(part).expanduser().resolve();target=base.resolve()
            if path==target or path.is_relative_to(target):matched.append(name);break
    return matched


def run(root,kind='historical',duration=4,model_python=None,work_root=None,profile_file='FINAL_NOTEBOOK_PROFILE.json',workers=6):
    if headless_markers(root):
        raise RuntimeError('Native replay is blocked in the saved-analysis headless context. Use a clean GUI kernel or the separately certified finite CLI.')
    return _base.run(root,kind=kind,duration=duration,model_python=model_python,work_root=work_root,profile_file=profile_file,workers=workers)
