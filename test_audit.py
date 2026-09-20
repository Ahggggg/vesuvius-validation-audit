"""Synthetic-only regression tests. No scroll metadata is included in this file."""
import argparse, hashlib, json, tempfile
from pathlib import Path
from upstream import load, segment, checked_sources
from audit import evaluate, metadata_status
from patch_loader import patched_source

CASES={
 'no_mask':['sample_inklabels.zarr','sample_supervision_mask.zarr'],
 'accepted_v2':['sample_inklabels_v2.zarr','sample_supervision_mask_v2.zarr','sample_validation_mask_v2.zarr'],
 'wrong_prefix':['sample_inklabels.zarr','sample_supervision_mask.zarr','foreign_validation_mask.zarr'],
 'unsupported_extension':['sample_inklabels.zarr','sample_supervision_mask.zarr','sample_validation_mask.png'],
 'other_supported_format':['sample_inklabels.zarr','sample_supervision_mask.zarr','sample_validation_mask.tif'],
 'same_version_absence':['sample_inklabels.zarr','sample_supervision_mask.zarr','sample_inklabels_v2.zarr','sample_supervision_mask_v2.zarr','sample_validation_mask_v2.zarr'],
 'missing_pair':['sample_validation_mask_v2.zarr'],
 'malformed_metadata':['sample_inklabels.zarr','sample_supervision_mask.zarr','sample_validation_mask.zarr'],
}

def run(source_dir):
    before,after=load(source_dir),load(source_dir,patched=True)
    rows=[]
    with tempfile.TemporaryDirectory(prefix='validation-audit-') as tmp:
        for case,names in CASES.items():
            directory=Path(tmp)/case/'sample'
            directory.mkdir(parents=True)
            for name in names:
                path=directory/name
                if path.suffix=='.zarr': path.mkdir()
                else: path.write_bytes(b'')
            if case=='malformed_metadata':
                (directory/'sample_validation_mask.zarr'/'.zattrs').write_text('{broken')
                assert any(r['status']=='malformed' for r in metadata_status(directory))
            for version in (None,'v1','v2'):
                for required in (True,False):
                    old=evaluate(before,directory,version,required=required)
                    new=evaluate(after,directory,version,required=required)
                    ignored=evaluate(after,directory,version,required=required,discarded_validation_policy='ignore')
                    strict=evaluate(after,directory,version,required=required,require_validation=True)
                    error_policy=evaluate(after,directory,version,required=required,discarded_validation_policy='error')
                    assert old==ignored, (case,version,'ignore changed behavior')
                    assert old['selected']==new['selected'] and old['error']==new['error'],(case,version,'changed selection')
                    assert old['warnings']==[] and old['stdout']==old['stderr']=='', 'upstream unexpectedly noisy'
                    selected=old['selected'] or {}
                    mask=selected.get('validation_mask')
                    candidates=after['audit_validation_candidates'](segment(after,directory,version),selected=directory/mask if mask else None)
                    missing=old['error'] is None and mask is None
                    assert bool(new['warnings']) == bool(missing and candidates),(case,version,'wrong warning')
                    assert bool(strict['error']) == bool(old['error'] or not mask),(case,version,'strict escaped')
                    assert bool(error_policy['error']) == bool(old['error'] or (missing and candidates))
                    if case=='wrong_prefix': assert 'prefix' in candidates[0]['reasons']
                    if case in ('unsupported_extension','other_supported_format'): assert 'format' in candidates[0]['reasons']
                    if case=='same_version_absence' and version=='v1': assert 'version' in candidates[0]['reasons']
                    rows.append({'case':case,'version':version,'required':required,'before':old,'after':new,'ignore':ignored,'strict':strict,'error_policy':error_policy,'candidates':candidates})
            invalid=evaluate(after,directory,discarded_validation_policy='typo')
            assert invalid['error'], 'invalid policy accepted'
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source-dir',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--seed',type=int,default=7)
    args=ap.parse_args()
    rows=run(args.source_dir)
    result={'seed':args.seed,'cases':len(CASES),'cells':len(rows),'null_baseline':'no_mask','rows':rows}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'synthetic_cases':len(CASES),'cells':len(rows),'all_passed':True},sort_keys=True))
if __name__=='__main__': main()
