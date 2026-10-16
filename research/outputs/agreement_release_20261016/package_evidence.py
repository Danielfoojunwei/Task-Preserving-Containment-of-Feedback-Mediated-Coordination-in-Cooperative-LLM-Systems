#!/usr/bin/env python3
"""Package these three studies and their offline checks without any API access."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[3]
PREFIX = "agreement-evidence-20261016"
STUDIES = ["agreement_pilot_20261015", "agreement_capability_20261015",
           "agreement_adversarial_20261015", "agreement_confirmation_20261015",
           "agreement_release_20261016"]

RESTORE = '''#!/usr/bin/env python3
"""Verify archived bytes and restore recorded local mtimes, not external attestation."""
import hashlib, json, os
from pathlib import Path
root = Path(__file__).resolve().parent
manifest = json.loads((root / "SOURCE_MANIFEST.json").read_text())
for name, entry in manifest["files"].items():
    path = (root / name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise SystemExit("Invalid archive path: " + name)
    if path.stat().st_size != entry["size"] or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
        raise SystemExit("Byte verification failed: " + name)
for name, entry in manifest["files"].items():
    os.utime(root / name, ns=(entry["mtime_ns"], entry["mtime_ns"]))
print(json.dumps({"files_verified":len(manifest["files"]),"recorded_local_mtimes_restored":True,"api_calls":0}))
'''

README = '''# Agreement evidence release

Start with `research/outputs/agreement_release_20261016/REPORT.md` or open
`replay.html` beside it. The requested covert agreement was not demonstrated.
The package retains all 300 calls, three cohort protocols, blinded judgments,
negative cases, settlement replay and independent verification.

`agreement_confirmation_20261015` is an **unrun draft**, with no calls or results.
This is a focused evidence package, not the whole project's earlier studies.
The separate metadata experiments are summarized in the report but not bundled.

No API key is included. Offline reconstruction needs Python 3.11+; runner tests
also need `jsonschema==4.26.0`. Visualization rebuild needs matplotlib. No model
call is made by the following commands. Do not invoke a runner's `--run` option.

ZIP extraction does not preserve nanosecond file times. First verify all source
bytes and restore their recorded local mtimes, used by the independent temporal
consistency checks:

```sh
python restore_and_verify.py
python -m unittest discover -s research/outputs/agreement_pilot_20261015 -p 'test_pilot.py' -q
python -m unittest discover -s research/outputs/agreement_capability_20261015 -p 'test_pilot.py' -q
python -m unittest discover -s research/outputs/agreement_adversarial_20261015 -p 'test_pilot.py' -q
python research/outputs/agreement_pilot_20261015/independent_verify.py --output-dir /tmp/agreement-original-check
python research/outputs/agreement_pilot_20261015/independent_verify.py --root research/outputs/agreement_capability_20261015 --output-dir /tmp/agreement-capability-check
python research/outputs/agreement_pilot_20261015/independent_verify.py --root research/outputs/agreement_adversarial_20261015 --output-dir /tmp/agreement-adversarial-check
```

Restoring source metadata does not independently authenticate creation order.
The hash/time freezes and provider records are local evidence; no public
preregistration or external temporal attestation is claimed. Historical absolute
paths in provenance identify the original workspace, while the verifier resolves
the bundled sources relative to each study. Verification outputs go to `/tmp`
so the archived evidence remains unchanged.

All observations predate the October 23–25 sprint and must be disclosed as prior
work. The report is AI-assisted research documentation, not final team-authored
submission prose. Trusted receipt-bound enforcement is established engineering;
no first-ever general collusion-prevention claim is made.
'''


def build(destination: Path):
    files = []
    for name in STUDIES:
        files += [p for p in (ROOT / "research/outputs" / name).rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts
                  and p.name != ".call.lock" and not p.name.endswith((".pyc", ".partial"))]
    files.append(ROOT / "research/outputs/controlplane_20261015/api_client.py")
    files = sorted(set(files))
    manifest = {str(p.relative_to(ROOT)): {
        "size": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        "mtime_ns": p.stat().st_mtime_ns} for p in files}
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            archive.write(path, PREFIX + "/" + str(path.relative_to(ROOT)))
        archive.writestr(PREFIX + "/SOURCE_MANIFEST.json", json.dumps({
            "git_head_at_packaging": commit, "files": manifest,
            "scope": "Focused three-cohort evidence; no API credentials or earlier full-project datasets."}, indent=2))
        archive.writestr(PREFIX + "/restore_and_verify.py", RESTORE)
        archive.writestr(PREFIX + "/README_REPRODUCE.md", README)
    return {"archive": str(destination), "files": len(files), "bytes": destination.stat().st_size,
            "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(), "git_head": commit}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    print(json.dumps(build(parser.parse_args().out), indent=2))
