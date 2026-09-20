"""Execute only filename-discovery declarations from hash-verified upstream sources."""
import ast
import hashlib
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
PIN = 'f07d33be6a00d12ace7d6a9465efe17c78ed7b47'
BLOBS = {'segment.py':'488dc669995dfaa3193171a511505053828bcdec','types.py':'e32dc90365f874e6b8aee5300f4a39aa5c0ce221'}

def blob(data):
    return hashlib.sha1(b'blob %d\0'%len(data)+data).hexdigest()

def checked_sources(source_dir):
    result = {}
    for name, expected in BLOBS.items():
        data = (Path(source_dir)/name).read_bytes()
        if blob(data) != expected:
            raise ValueError('Source Git blob mismatch: '+name)
        result[name] = data.decode('utf-8')
    return result

def load(source_dir, patched=False):
    sources=checked_sources(source_dir)
    ns={'dataclass':dataclass,'replace':replace,'Path':Path,'InkDataConfig':SimpleNamespace,'DatasetSource':SimpleNamespace}
    type_tree=ast.parse(sources['types.py'])
    segment_class=next(n for n in type_tree.body if isinstance(n,ast.ClassDef) and n.name=='Segment')
    exec(compile(ast.Module(body=[segment_class],type_ignores=[]),'<pinned Segment>','exec'),ns)
    text=sources['segment.py']
    if patched:
        from patch_loader import patched_source
        text=patched_source(text)
    tree=ast.parse(text)
    chosen=[]
    for node in tree.body:
        if isinstance(node,(ast.Assign,ast.AnnAssign)):
            chosen.append(node)
        elif isinstance(node,ast.FunctionDef) and node.name in ('parse_label_asset_path','discover_segment_labels','_discover_segment_labels','audit_validation_candidates'):
            chosen.append(node)
    exec(compile(ast.Module(body=chosen,type_ignores=[]),'<pinned discovery'+(' patched' if patched else '')+'>','exec'),ns)
    return ns

def segment(ns, directory, version=None, name=None):
    directory=Path(directory)
    return ns['Segment'](data_config=SimpleNamespace(label_version=version),source=SimpleNamespace(),dataset_idx=0,segment_relpath=directory.name,segment_dir=directory,segment_name=name or directory.name,image_volume=directory/(directory.name+'.zarr'))

