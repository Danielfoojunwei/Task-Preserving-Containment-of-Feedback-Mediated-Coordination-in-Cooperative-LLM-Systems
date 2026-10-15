# Post hoc field-validity sensitivity

Endpoint decomposition was selected after the completed study's audit revealed checksum-domain failures. It was not preregistered. All frozen confirmation results remain unchanged; even adjusted sensitivity p-values are exploratory.

This analysis reads saved outputs only. The main analyzer, its primary endpoint and its null family-corrected findings are unchanged. All 32 mini worlds and all sender errors remain included. No model call was repeated.

| Carrier | Whole-domain ΔS | Raw decoded-bit-only ΔS | Raw 95% world-bootstrap CI | Raw exact p | Raw descriptive Holm p |
|---|---:|---:|---|---:|---:|
| policy_label | +0.015625 | +0.015625 | [-0.015625, +0.046875] | 0.625 | 0.625 |
| numeric_receipt | +0.117188 | +0.218750 | [+0.109375, +0.320312] | 0.00089933723 | 0.0026980117 |
| rejection_status | +0.101562 | +0.218750 | [+0.140625, +0.296875] | 2.0980835e-05 | 8.392334e-05 |
| joint_xor | +0.035156 | +0.027344 | [-0.003906, +0.062500] | 0.171875 | 0.34375 |

Of 1456 receiver records, 476 fail the complete domain parser. 98 contain a numeric raw decoded bit suppressed by that validation: 65 correct and 33 wrong. These counts include all study kinds and both models; detailed cells and all receiver provenance are in the JSON.

Raw proposed route payoffs are evaluated separately in the JSON. They are proposals the host rejected where whole-domain validity failed. They must never be described as executed attacks, and neither raw bit accuracy nor private-information recovery alone establishes profitable harm.

Bootstrap resampling clusters complete public worlds; XOR pads are averaged before world comparisons. Null decoded bits contribute q=0.5. The joint comparator remains marginal_guard versus transcript_guard; the three single-carrier comparators remain payload_only versus transcript_guard. The four-way Holm display does not turn this selected-after-audit endpoint into confirmation.
