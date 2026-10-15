# Independent primary-analysis replication

All four registered primary statistics, exact p-values, Holm adjustment and 20,000-resample bootstrap intervals were reproduced from raw receiver records. This implementation uses rational numbers and grouped binomial polynomials, independently of the frozen analyzer’s stepwise DP. No frozen file was changed.

| Carrier | Lower-scope comparator | Public worlds | Mean | Exact p | Holm p |
|---|---|---:|---:|---:|---:|
| policy_label | payload_only | 32 | +0.01562 | 0.625 | 0.625 |
| numeric_receipt | payload_only | 32 | +0.11719 | 0.06206942 | 0.125 |
| rejection_status | payload_only | 32 | +0.10156 | 0.03173828 | 0.125 |
| joint_xor | marginal_guard | 32 | +0.03516 | 0.03125 | 0.125 |

Inventory: 400 distinct main source calls; 1,200 main receiver records; 80 crossed, 48 boundary, 32 cooperative and 96 adaptive receiver records. Frozen files verified: 64.

Secret twins and pads remain clustered within public worlds. Primary and exploratory transfer models are not pooled. Observed full-guard transcript equality: True; full model-request equality: True. These are observed-input checks, distinct from the exhaustive finite certificate and independent provider audit.
