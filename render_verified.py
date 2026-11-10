"""Call unchanged frozen renderer on a verified portable-reader payload."""
import argparse,hashlib,importlib.abc,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PINS={'render.py':'4040740e28a93cc2cea9bd2ec716506bf7086ad4fc6c245b3e571c3d822a4e7c','gate.py':'efdf5392cc148ce4b14b7baeea2c5e718b299e64ae7de1b97fb2ae1aa9c55b02','source_pins.json':'51a176741e38852deb60afffad7394d444b22f15b0275e920fe8d303ba4c5776'}
class DenyModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,path=None,target=None):
        if name=='fish_sim' or name.startswith('fish_sim.') or name=='cmodel':raise RuntimeError('No model imports in rendering')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--data-sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert sha(a.data)==a.data_sha256,'Verified reporter payload changed'
    folder=ROOT/'validation_tools/validation_reporting'
    for name,digest in PINS.items():assert sha(folder/name)==digest,name
    sys.meta_path.insert(0,DenyModel());sys.path.insert(0,str(folder))
    import render
    data=json.loads(a.data.read_text());assert data['stage']=='final' and data['school_count']==16 and len(data['rows'])==192
    receipt=render.export(data,a.output)
    assert not any(n=='fish_sim' or n.startswith('fish_sim.') or n=='cmodel' for n in sys.modules)
    print(json.dumps(dict(status=receipt['status'],synthetic=receipt['synthetic'],native_steps=0,new_bootstrap_draws=0)))
if __name__=='__main__':main()
