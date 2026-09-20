"""Read-only filename audit against exact pinned upstream discovery functions."""
import argparse, contextlib, hashlib, io, json, warnings
from pathlib import Path
from upstream import load, segment, PIN, BLOBS

KINDS=('inklabels','supervision_mask','validation_mask')
def evaluate(ns,directory,version=None,**kwargs):
    result={'selected':None,'error':None}
    out,err=io.StringIO(),io.StringIO()
    with warnings.catch_warnings(record=True) as caught,contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
        warnings.simplefilter('always')
        try:
            selected=ns['discover_segment_labels'](segment(ns,directory,version),**kwargs)
            result['selected']={k:(getattr(selected,k).name if getattr(selected,k) else None) for k in KINDS}
        except ValueError as exc:
            result['error']=str(exc).replace(str(directory),'<SEGMENT_DIR>')
    result.update(warnings=[str(w.message) for w in caught],stdout=out.getvalue(),stderr=err.getvalue())
    return result

def metadata_status(directory):
    """JSON syntax checks only; never read array chunks or infer mask coverage."""
    rows=[]
    for asset in sorted(Path(directory).iterdir()):
        if not asset.is_dir() or asset.suffix.lower()!='.zarr': continue
        for rel in ('.zattrs','0/.zarray'):
            path=asset/rel
            row={'asset':asset.name,'metadata':rel,'status':'absent'}
            if path.exists():
                data=path.read_bytes()
                row['sha256']=hashlib.sha256(data).hexdigest()
                try:
                    value=json.loads(data)
                    row['status']='json_object' if isinstance(value,dict) else 'malformed'
                except (ValueError,UnicodeError): row['status']='malformed'
            rows.append(row)
    return rows

def audit(source_dir,directory,version=None,required=True,require_validation=False,policy='warn'):
    ns=load(source_dir,patched=True)
    outcome=evaluate(ns,directory,version,required=required,require_validation=require_validation,discarded_validation_policy=policy)
    selected=outcome['selected'] or {}
    mask=selected.get('validation_mask')
    return {'source_commit':PIN,'source_blobs':BLOBS,'scope':'filename discovery and optional JSON metadata only; no chunks read',
            'requested_version':version,'required_validation':require_validation,'outcome':outcome,
            'validation_candidates':ns['audit_validation_candidates'](segment(ns,directory,version),selected=Path(directory)/mask if mask else None),
            'metadata':metadata_status(directory)}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('directory',type=Path)
    ap.add_argument('--source-dir',required=True,type=Path)
    ap.add_argument('--version')
    ap.add_argument('--require-validation',action='store_true')
    ap.add_argument('--optional-labels',action='store_true')
    ap.add_argument('--discarded-validation-policy',choices=['warn','error','ignore'],default='warn')
    args=ap.parse_args()
    result=audit(args.source_dir,args.directory,args.version,not args.optional_labels,args.require_validation,args.discarded_validation_policy)
    print(json.dumps(result,indent=2,sort_keys=True))
    return 2 if result['outcome']['error'] else 0
if __name__=='__main__': raise SystemExit(main())
