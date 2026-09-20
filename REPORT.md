# Validation asset audit: behavior and evidence

The audit explains why villa selects no validation mask when a candidate is rejected by filename prefix, format, or requested version. The patch preserves the upstream selection and adds a warning when candidates exist but none is selected. Optional strict validation refuses missing validation, including genuine absence. It does not substitute rejected masks.

The target is [villa commit f07d33be6a00d12ace7d6a9465efe17c78ed7b47](https://github.com/ScrollPrize/villa/commit/f07d33be6a00d12ace7d6a9465efe17c78ed7b47). The harness checks the source Git blob IDs listed in README.md and executes the exact upstream declarations with minimal configuration stubs. It loads no training modules or array chunks.

## Synthetic before/after example

The existing `same_version_absence` case in `test_audit.py` creates a directory named `sample` containing five empty directories:

```text
sample_inklabels.zarr
sample_supervision_mask.zarr
sample_inklabels_v2.zarr
sample_supervision_mask_v2.zarr
sample_validation_mask_v2.zarr
```

With version `v1` requested and labels required, the completed regression check establishes this behavior:

| Behavior | Original loader | Patched loader |
|---|---|---|
| Ink and supervision selection | Unversioned pair (v1) | Same pair |
| Validation selection | None | None |
| Default diagnostic | Silent | Warning identifies rejected v2 candidate |
| Explicit ignore policy | Original behavior | Same selections and silence |

The audit reports `version` as the candidate's rejection reason. With `--require-validation`, the patched audit returns a loader error and exit code 2. Default warnings remain in JSON with exit code 0. With no explicit version, or with `v2`, this fixture selects the v2 validation mask and the patch preserves that selection. These are synthetic filename checks, not measurements of mask contents.

## Completed checks

The implementation suite passed 48 combinations: eight synthetic cases, three version choices, and two required-label settings. It covered genuine absence, accepted v2 validation, wrong prefix, unsupported PNG, excluded TIFF, explicit-version absence, missing required labels, and malformed metadata. It checked selection parity, warning/error/ignore policies, and strict refusal.

A separate AI reviewer recorded expected cases before inspecting implementation tests or results and reproduced 89/89 software contract checks. These included optional labels, duplicate versions, invalid policies, extension/case variants, CLI JSON and exit behavior, and application of the final patch to the pinned source. The independent review harness is not bundled; the included implementation suite is reproducible using the README commands. Packaging changed documentation and licensing only; executable files and tests are unchanged, and finished tests were not rerun for packaging.

## Limits and related work

Selection does not establish valid metadata schema, compatible dimensions, available chunks, a nonempty held-out region, or freedom from sampling leakage. Malformed JSON may still be filename-selectable; the audit reports its syntax separately. Existing independent greatest-version selection across label kinds is preserved. Strict validation is opt-in and is not connected to the training CLI. No training performance, improved reading, or recovered text is established by these checks.

Related [villa issue #1231](https://github.com/ScrollPrize/villa/issues/1231) concerns unpublished validation masks and evaluation tooling. This contribution diagnoses existing candidates that are discarded. The limited prior-art review does not establish novelty.

## Authorship and review

Implementation, tests, documentation, and the separate software review were AI-assisted. Separate-agent review is not independent human review or scientific validation. No independent human or scientific review is claimed. The contribution is MIT licensed; upstream copyright and permission notices are retained in THIRD_PARTY_NOTICES.txt.
