"""Logical notebook verification; outputs and Jupyter metadata are transient."""
from __future__ import annotations
import ast,copy,hashlib,json
from pathlib import Path

DEFAULTS={'RUN_NATIVE':False,'NATIVE_DURATION_T':4,'NATIVE_ARTIFACT':'historical','NATIVE_WORKERS':6}

def source(cell):
    value=cell.get('source',[])
    return value if isinstance(value,str) else ''.join(value)

def config_value(name,node):
    if not isinstance(node,ast.Constant):raise ValueError('Use literal notebook setting:'+name)
    value=node.value
    valid=(type(value)is bool if name=='RUN_NATIVE' else
           type(value)is int and value in (4,36) if name=='NATIVE_DURATION_T' else
           type(value)is str and value in ('historical','source-built') if name=='NATIVE_ARTIFACT' else
           type(value)is int and value in range(1,7))
    if not valid:raise ValueError('Invalid typed notebook setting:'+name)
    return value

def canonical_ast(value):
    # ast.dump changed its empty-field display in Python3.13. Serialize the
    # actual AST fields explicitly, rather than pinning a printer's format.
    if isinstance(value,ast.AST):return [type(value).__name__,{name:canonical_ast(getattr(value,name,None))for name in value._fields}]
    if isinstance(value,list):return [canonical_ast(item)for item in value]
    return value

def logical(book,configuration_cell_id):
    result=[];configuration=None
    for cell in book.get('cells',[]):
        kind=cell.get('cell_type');identifier=cell.get('id')
        if kind not in ('code','markdown') or not isinstance(identifier,str):raise ValueError('Notebook cell inventory differs')
        text=source(cell)
        if kind=='code':
            tree=ast.parse(text);tree=copy.deepcopy(tree)
            if identifier==configuration_cell_id:
                if configuration is not None:raise ValueError('Duplicate native configuration cell')
                configuration={}
                if len(tree.body)<len(DEFAULTS):raise ValueError('Missing native configuration assignments')
                for node,name in zip(tree.body,list(DEFAULTS)):
                    if not isinstance(node,ast.Assign) or len(node.targets)!=1 or not isinstance(node.targets[0],ast.Name) or node.targets[0].id!=name:raise ValueError('Only declared leading literal settings may change')
                    configuration[name]=config_value(name,node.value)
                    node.value=ast.Constant(DEFAULTS[name])
            normal=json.dumps(canonical_ast(tree),sort_keys=True,separators=(',',':'))
        else:normal=text
        result.append(dict(id=identifier,cell_type=kind,logical_source=normal))
    if configuration is None:raise ValueError('Native configuration cell missing')
    return result,configuration

def verify(active_path,template_path,configuration_cell_id,expected_logical_sha256):
    active=json.loads(Path(active_path).read_text());template=json.loads(Path(template_path).read_text())
    canonical,defaults=logical(template,configuration_cell_id);actual,settings=logical(active,configuration_cell_id)
    digest=hashlib.sha256(json.dumps(canonical,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if digest!=expected_logical_sha256:raise ValueError('Immutable notebook template logical digest differs')
    if actual!=canonical:raise ValueError('Notebook logical source/cell inventory changed; restore the canonical template')
    return dict(status='logical_source_verified',logical_sha256=digest,settings=settings,cells=len(actual),code_cells=sum(c['cell_type']=='code'for c in actual),transient_outputs_execution_counts_and_metadata_ignored=True)
