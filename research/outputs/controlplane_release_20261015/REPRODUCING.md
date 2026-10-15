# Reproduce both control-plane studies

The dataset preserves original model requests, raw responses, transport attempts, world truth, source reuse, complete receiver transcripts, protocols, frozen source hashes and the prior-art audit. Evaluator truth is not part of receiver prompts. No API key is included.

Use Python 3.11 with NumPy 2.2.6 and jsonschema 4.26.0. Matplotlib 3.10.8 is required only to regenerate figures. Verify the archive against `ARTIFACT_SHA256.json` before changing anything. The manifest excludes itself; the ZIP has an external SHA-256 sidecar.

Run the frozen analysis on a new copy, without any paid model calls:

```bash
python reproduce_offline.py --out /tmp/controlplane-reproduced
```

The wrapper copies both `controlplane_20261015` and `hostmask_20261015` as sibling directories into a new output directory. It disables the network routes used by this code, regenerates both frozen analyses, checks that every primary result is identical, and verifies that the original evidence files did not change. Paths and report timestamps may differ. Statistical units are public-world blocks, averaging pads within each joint-channel block. The release includes the verification record from an actual offline run.

Software checks make zero provider calls:

```bash
cd controlplane_20261015
python -m unittest -q test_api_client test_integration
python finite_certificate.py
```

The second command writes a fresh certificate; perform checks on a copy if preserving the extracted file timestamps/manifest is required. The finite certificate covers the registered interface, not external timing, billing, or arbitrary tools. Exact receiver-query reconstruction is documented by `FINAL_AUDIT.json`; the evidence auditor is provided in `audit_controlplane.py`.

`run_controlplane.py --run` makes paid API calls and requires the environment credential. It is not an offline reproduction command. Existing final requests/responses are immutable. A new independent replication should use a new output directory, compatible provider schemas, and a newly frozen protocol; do not change the original frozen evidence to obtain a more favorable result.

Six pre-research compatibility requests are retained separately. Two failed with HTTP400 because the providers rejected the initial array-enumeration schema; the primitive wire schema then passed. Exact permutation/range checks remain in host domain parsers. Research responses failing domain validation stay in the analysis, and completed outcomes are never retried for improvement.

The follow-up's `run_hostmask.py --self-test` is also an offline check; use a copy. `run_hostmask.py --run` makes paid calls and must not be used for offline reproduction. The follow-up was designed after the main null findings, source-encoding errors and task-scoring issue were known. Its six-file freeze preceded its own 368 calls. Do not pool its primary with the original family or describe it as a retrospective repair. The successful public task in that follow-up is copying supplied canonical values.

Source claims and limits are in `controlplane_20261015/LITERATURE_POSITIONING.md` and the manuscript. This is a new synthetic causal evaluation and finite mediation example, not a full reproduction of CaMeL, FIDES, FLOWSEAL, OCELOT or OrchDebate. XOR composition and noninterference are established concepts; the new empirical claims must be judged from the actual live outcomes.
