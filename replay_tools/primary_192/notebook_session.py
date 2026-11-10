"""Versioned package-path check; all frozen saved-analysis methods are inherited.

The prior main is retained byte-exact in an archive. Its old manifest and every
other original input stay unchanged. Only the mutable notebook entry migrates.
"""
from pathlib import Path
from integration import Session as OriginalSession, read, sha, relative, require
from integration import READER_SHA,RENDER_SHA,GATE_SHA,PINS_SHA

OLD_MANIFEST_SHA='a30927d7a62dc56f1d23b5c7bf2d77a663ac6892f9b40712e03ec2e69d48e3cd'
OLD_MAIN_SHA='763887eccb331dbc506064843e5334707bb834def5dc9b89059852a07e57617c'

class Session(OriginalSession):
    def verify_package(self):
        require(sha(self.root/'PACKAGE_INPUTS.json')==OLD_MANIFEST_SHA,'Original package manifest changed')
        original=read(self.root/'PACKAGE_INPUTS.json')
        binding=read(self.root/'NOTEBOOK_RELEASE_BINDINGS.json')
        require(binding.get('schema')=='fishsim_postcert_notebook_bindings_v1','Unknown notebook release binding')
        require(binding.get('original_package_manifest_sha256')==OLD_MANIFEST_SHA,'Original package binding differs')
        require(original['files'].get('main.ipynb')==OLD_MAIN_SHA,'Original main binding differs')
        archive=relative(self.root,binding['original_main_archive'])
        require(sha(archive)==OLD_MAIN_SHA,'Archived original main changed')
        for name,digest in original['files'].items():
            path=archive if name=='main.ipynb' else relative(self.root,name)
            require(sha(path)==digest,'Preserved original package input changed:'+name)
        require('main.ipynb' not in binding['files'],'Active notebook raw bytes must remain editable by Jupyter')
        for name,digest in binding['files'].items():
            require(sha(relative(self.root,name))==digest,'Post-cert notebook input changed:'+name)
        require(sha(self.root/'validation_tools/portable_reader.py')==READER_SHA,'Pinned portable reader changed')
        for name,digest in [('render.py',RENDER_SHA),('gate.py',GATE_SHA),('source_pins.json',PINS_SHA)]:
            require(sha(self.root/'validation_tools/validation_reporting'/name)==digest,'Frozen reporter changed:'+name)
        from .notebook_template import verify
        template=binding['notebook_template']
        self.logical_notebook_validation=verify(self.root/'main.ipynb',relative(self.root,template['path']),template['configuration_cell_id'],template['logical_sha256'])
        self.input_files=len(original['files'])+len(binding['files'])
        return self.input_files
