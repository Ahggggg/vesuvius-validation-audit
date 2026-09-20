"""Minimal source-preserving upstream patch: selection stays byte-for-byte intact."""
import argparse
import difflib
from pathlib import Path
from upstream import checked_sources

ADDITION = '''

def audit_validation_candidates(segment: Segment, *, extension: str = ".zarr", selected=None):
    """Report filename candidates; a rejected file is not proof of a usable mask."""
    import re
    rows = []
    requested = segment.data_config.label_version
    for path in sorted(segment.segment_dir.iterdir()):
        match = re.fullmatch(r"(.*)_validation_mask(?:_v([0-9]+))?(\\.[^.]+)", path.name)
        if match is None:
            continue
        prefix, version, suffix = match.groups()
        reasons = []
        if prefix != segment.segment_name:
            reasons.append("prefix")
        if suffix.lower() not in _LABEL_EXTENSIONS or suffix.lower() != str(extension).lower():
            reasons.append("format")
        if requested and requested != f"v{int(version or 1)}":
            reasons.append("version")
        is_selected = selected is not None and path == selected
        if not reasons and not is_selected:
            reasons.append("not_selected")
        rows.append({"name": path.name, "prefix": prefix, "version": f"v{int(version or 1)}",
                     "extension": suffix.lower(), "selected": is_selected, "reasons": reasons})
    return rows


def discover_segment_labels(
    segment: Segment, *, extension: str = ".zarr", required: bool = True,
    discarded_validation_policy: str = "warn", require_validation: bool = False,
) -> Segment:
    """Preserve label selection and make an unavailable validation mask explicit.

    require_validation checks selection only, not array contents or patch counts.
    Intentional no-validation callers may explicitly use policy="ignore".
    """
    if discarded_validation_policy not in {"warn", "error", "ignore"}:
        raise ValueError("discarded_validation_policy must be warn, error, or ignore")
    selected = _discover_segment_labels(segment, extension=extension, required=required)
    if selected.validation_mask is not None:
        return selected
    candidates = audit_validation_candidates(segment, extension=extension)
    if require_validation or (candidates and discarded_validation_policy == "error"):
        raise ValueError(
            f"Validation unavailable for {segment.segment_name}; requested version="
            f"{segment.data_config.label_version!r}, extension={extension!r}; "
            f"candidates={candidates!r}"
        )
    if candidates and discarded_validation_policy == "warn":
        import warnings
        warnings.warn(
            f"Validation candidates discarded for {segment.segment_name}; requested version="
            f"{segment.data_config.label_version!r}, extension={extension!r}; "
            f"candidates={candidates!r}", RuntimeWarning, stacklevel=2,
        )
    return selected
'''

def patched_source(original):
    marker='def discover_segment_labels('
    if original.count(marker)!=1:
        raise ValueError('Expected one upstream discover_segment_labels definition')
    changed=original.replace(marker,'def _discover_segment_labels(',1)
    return changed.replace('\n\ndef gather_segments(',ADDITION+'\n\ndef gather_segments(',1)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source_dir',type=Path)
    ap.add_argument('--patch',required=True,type=Path)
    args=ap.parse_args()
    original=checked_sources(args.source_dir)['segment.py']
    path='vesuvius/src/vesuvius/ink_detection/data/segment.py'
    diff=''.join(difflib.unified_diff(original.splitlines(True),patched_source(original).splitlines(True),fromfile='a/'+path,tofile='b/'+path))
    args.patch.write_text(diff,encoding='utf-8',newline='\n')
    print('Wrote '+str(args.patch))
if __name__=='__main__': main()
