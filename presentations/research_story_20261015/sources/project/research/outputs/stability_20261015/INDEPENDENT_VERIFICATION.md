# Independent stability-study verification

**PASSED_INDEPENDENT_RAW_RECONSTRUCTION**.

This verifier imports no study code and makes no API calls. It independently parses saved provider JSON, reconstructs fields and domain-valid actions, enumerates all 2^20 sign assignments, and checks actual wire hashes.

| Joint minus comparator | Mean signed-decoding effect | Exact p | Holm4 p |
|---|---:|---:|---:|
| joint_minus_full | 0.0875000 | 0.00021362305 | 0.00042724609 |
| joint_minus_label_only | 0.0937500 | 1.5258789e-05 | 6.1035156e-05 |
| joint_minus_receipt_only | 0.1031250 | 3.0517578e-05 | 9.1552734e-05 |
| joint_minus_donor_joint | 0.0687500 | 0.0035400391 | 0.0035400391 |

## Independently reconstructed announcement factorial

Each of the four factorial arms contains 80 actual calls: four balanced bit/pad cells in each of 20 independent worlds. Both signed decoding and accepted betting harm were reconstructed from raw replies, without using saved evaluator metrics. Every secondary effect, world-bootstrap interval, full-enumeration p-value and Holm6 value was compared with the frozen analysis.

| Endpoint | Contrast | Mean effect | Descriptive world-bootstrap95 | Exact p | Holm6 p |
|---|---|---:|---|---:|---:|
| signed_S | main_actual_view_joint_minus_full | 0.1156250 | [0.06875, 0.1625] | 0.0002746582 | 0.001373291 |
| signed_S | main_banner_marginal_minus_full | 0.0968750 | [0.059375, 0.134375] | 0.00036621094 | 0.001373291 |
| signed_S | interaction | 0.2312500 | [0.1375, 0.325] | 0.0002746582 | 0.001373291 |
| accepted_betting_owner_harm | main_actual_view_joint_minus_full | 1.1375000 | [0.56875, 1.6625] | 0.0023345947 | 0.0046691895 |
| accepted_betting_owner_harm | main_banner_marginal_minus_full | 3.1500000 | [2.45, 3.89375] | 1.9073486e-06 | 1.1444092e-05 |
| accepted_betting_owner_harm | interaction | 2.2750000 | [1.1375, 3.325] | 0.0023345947 | 0.0046691895 |

Source copying: 40/40. Logical calls: 1320/1320. Retries: 0. Frozen-analyzer comparison available: True.

Full source/case hashes, raw-parsing and action-validity counts, stochastic disagreement, source-snapshot ordering and actual request information laws are retained in INDEPENDENT_VERIFICATION.json.

This is a supplied-codebook synthetic inference assay with a neutral source and simple public copying task. It does not establish spontaneous collusion, general task preservation or zero population error rates.

Frozen sources were read only. Local file chronology is a consistency check, not external timestamp attestation.
