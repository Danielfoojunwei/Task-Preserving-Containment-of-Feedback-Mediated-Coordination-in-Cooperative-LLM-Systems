# Standalone offline reproduction

The ZIP preserves repository-relative paths. It contains the complete new
`research/outputs/covert_extension_20261016/` extension, except bytecode caches
and lock files, and only the transitive SHA256 dependency closure of
`formation/FREEZE.json` and `clarification/FREEZE.json`. The two JSON files store
their pins in their `sha256` members. `EXPORT_MANIFEST.json` lists every archived
source file's byte count and SHA256 and all 69 pinned paths. No Git metadata,
credential files, or unrelated repository directories are included.

Use Python 3.11 or newer on Linux. Reproduction uses the Python standard library
only. It needs no provider account, API access, package install, or network.
Existing source artifacts, audit releases, analyses and review seals remain
unchanged. New reproduction outputs must use previously nonexistent paths.

Extract into a new empty directory and run from its repository root:

```bash
python3 -m zipfile -e covert-extension-20261016.zip fresh-repository
cd fresh-repository
python3 research/outputs/covert_extension_20261016/release/package_extension.py \
  reproduce --repo-root "$PWD" --output-dir "$PWD/.offline-reproduction"
```

The reproduction launcher requires exactly the manifest file set, then verifies
all manifest hashes and all transitive freeze pins before execution. It starts a fresh Python process with an environment
allowlist that removes provider keys, cloud credentials, identity and proxy
headers, inherited Python paths, and credential-file selectors. `HOME` points to
an empty directory. A `PYTHONPATH` `sitecustomize.py` replaces socket entry points
and rejects Python socket audit events. Loaded study modules and inherited
dependency roots must resolve inside the extracted repository. The export-time
verification additionally forbids opening the original source repository and
asserts it is absent from `sys.path`; only extracted dependencies can be used.

The resulting `.offline-reproduction/OFFLINE_VERIFICATION.json` and logs record:

- 149 formation tests, 25 clarification tests, and the v2 secondary helper tests.
- Both source-freeze checks, including inherited freeze dependencies.
- A new exclusive all-phase independent raw audit under
  `formation/independent/offline_reproduction_all/`: all 1,430 formation calls,
  without overwriting the archived `independent/all/` release.
- A separate raw clarification self-check of all 64 calls, equal to the archived
  self-check, written under `.offline-reproduction/`.
- A primary analyzer rerun into a new output file. Its complete JSON record,
  including every scientific statistic, summary and session, must equal the
  archived analysis. No fields are ignored. It uses the unchanged, source-bound
  archived audit links; the fresh raw audit independently rechecks those sources.
- A v2 secondary remerge into a new output file, using the unchanged archived
  analysis and packet provenance. Its complete data must equal the archived
  secondary release, with no fields ignored.
- The independent results checker's synthetic checks and its full original-wire
  reconstruction into a new directory. The result must match the archived
  independent check, excluding only its newly generated timestamp.
- A final check that every archived source byte and every frozen pin is unchanged.

This reproduces the new extension and its source-bound analyses. Aggregate
budget closure uses the pinned prior-liability inventory and completion
certificate. The ZIP does not reconstruct every old cohort's raw-call costs;
those raw cohorts remain available in the earlier bundle. The pinned historical
world035 packet supports the clarification's provenance; it does not revise the
historical primary label. Source hashes establish local consistency, not an
external timestamp attestation. Semantic labels remain sealed assistant reviews.

To create a release after all extension files are final, run from the source
repository root:

```bash
python3 research/outputs/covert_extension_20261016/release/package_extension.py \
  build --repo-root "$PWD" --output /workspace/exports/covert-extension-20261016.zip
```

The build rejects existing archive and receipt paths, checks source hashes before
and after packaging, rejects path traversal and symlinks, safely extracts the ZIP
into a fresh temporary filesystem tree, and executes the isolated reproduction
from the extracted script. A successful build writes `.zip.sha256`,
`.zip.receipt.json` with exact archive bytes and SHA256, and a separate
`.zip.offline-verification/` evidence directory. The evidence directory contains
fresh outputs and logs; it is not an input to the ZIP. A failed verification
produces no success receipt. The build makes no API calls or Git mutations.
