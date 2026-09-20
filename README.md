# Validation asset audit

This small Python 3.10+ tool reports the label files selected by villa and validation candidates rejected by prefix, format or requested version. It adds a source-preserving patch to the real upstream loader. It needs only the Python standard library.

Supply `segment.py` and `types.py` from villa commit `f07d33be6a00d12ace7d6a9465efe17c78ed7b47` in one directory. They are not bundled. The tool verifies their Git blob IDs before executing only the exact `Segment`, parser and discovery declarations. Configuration objects are minimal stubs; no training modules, torch, arrays or chunks are loaded.

- `segment.py`: `vesuvius/src/vesuvius/ink_detection/data/segment.py`, Git blob `488dc669995dfaa3193171a511505053828bcdec`.
- `types.py`: `vesuvius/src/vesuvius/ink_detection/types.py`, Git blob `e32dc90365f874e6b8aee5300f4a39aa5c0ce221`.

From this directory, with your source and segment directories substituted:

```text
python test_audit.py --source-dir /path/to/pinned-source --output synthetic-results.json --seed 7
python audit.py /path/to/segment --source-dir /path/to/pinned-source --version v1
python audit.py /path/to/segment --source-dir /path/to/pinned-source --version v1 --require-validation
python patch_loader.py /path/to/pinned-source --patch validation.patch
```

The audit emits JSON with selected labels, candidate rejection reasons, captured warnings and errors, and optional metadata JSON syntax checks. Exit 0 means filename discovery returned; warnings are included in JSON and do not change the exit code. A loader error returns exit 2. `--require-validation` returns exit 2 whenever validation selection fails, including genuine absence. `--discarded-validation-policy error` fails when candidates exist but none is selected. `--discarded-validation-policy ignore` explicitly preserves intentional no-validation behavior. `--optional-labels` retains upstream `required=False` semantics; it does not override `--require-validation`.

Apply `validation.patch` at the pinned villa repository root with `git apply --check /path/to/validation.patch` followed by `git apply /path/to/validation.patch`. The patch renames the existing selector to `_discover_segment_labels` and wraps it; its selection body is unchanged. Existing callers receive a RuntimeWarning only when candidates exist but selection yields no validation mask. Callers can set keyword arguments `require_validation=True` or `discarded_validation_policy="error"|"ignore"`. Strict validation is opt-in; this does not connect a new flag to the training CLI.

The synthetic suite covers 48 combinations: eight cases, three version choices, and two required-label settings. Each checks unchanged selections and explicit ignore behavior, default diagnostics, strict refusal and the error policy. Cases include genuine absence, accepted v2, wrong prefix, unsupported PNG, excluded TIFF, explicit-version absence, missing required label pair and malformed JSON metadata. No real filenames or metadata are embedded in the tests.

Selection is not array validation. A selected mask can still have malformed metadata, missing chunks, incompatible dimensions or zero held-out patches. The audit reports JSON syntax without asserting metadata schema or pixel coverage. Default upstream independent greatest-version selection is preserved, including its existing possibility of different versions across label kinds; the patch never substitutes a rejected candidate.

`audit.py`, `upstream.py`, `patch_loader.py` and `test_audit.py` are the validation-asset-audit contribution. `validation.patch` contains our changes plus small upstream context. Upstream villa is MIT licensed, copyright (c) 2024 Vesuvius Challenge; its pinned [LICENSE](https://github.com/ScrollPrize/villa/blob/f07d33be6a00d12ace7d6a9465efe17c78ed7b47/LICENSE) was inspected on 2026-09-20. The complete upstream copyright and permission notice is included in THIRD_PARTY_NOTICES.txt. Our contribution is licensed under the MIT License in LICENSE. See REPORT.md for the synthetic before/after example, completed checks, limitations, related work, and AI-assisted authorship and review. This package contains code, synthetic tests, and documentation; the pinned upstream source files must be supplied separately.

