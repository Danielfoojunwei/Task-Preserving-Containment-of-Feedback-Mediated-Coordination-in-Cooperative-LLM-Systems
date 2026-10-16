# Released supplemental tables

Fresh 8-block randomized negotiation-scaffolding supplement. Action gain and manually evidenced agreement are separate outcomes.

## Supplemental primary family

| Contrast | Blocks | Mean Δ | Descriptive 95% CI | Raw exact p | Holm (2) p | Joint Holm (5) p |
|---|---:|---:|---|---:|---:|---:|
| directed - plain | 8 | 0.458309 | [0.244519, 0.628770] | 0.03125000 | 0.06250000 | 0.15625000 |
| directed - directed_no_notes | 8 | 0.303547 | [0.080556, 0.524281] | 0.12500000 | 0.12500000 | 0.50000000 |

The 20,000-bootstrap intervals are descriptive and not multiplicity-adjusted. Exact tests enumerate all 256 swaps. The inference unit is the randomized matched block, not a round, action or judge call.

## Arm descriptions

| Arm | Sessions / rounds | Primary mean | Gross / net owner loss | Both-positive rounds | Coverage A / B | Correct sorting |
|---|---|---:|---:|---|---|---|
| plain | 8 / 32 | 0.080556 | 46 / 34.50 | 4/32 | 1.0000 / 1.0000 | 101/128 |
| directed | 8 / 32 | 0.538864 | 307 / 230.25 | 28/32 | 1.0000 / 1.0000 | 99/128 |
| directed_no_notes | 8 / 32 | 0.235317 | 163 / 122.25 | 12/32 | 1.0000 / 1.0000 | 101/128 |

## Separate joint five-contrast accounting

| Study | Contrast | Matched blocks | Raw exact p | Joint Holm (5) p |
|---|---|---:|---:|---:|
| parent | full - no_notes | 16 | 1.00000000 | 1.00000000 |
| parent | full - no_feedback | 16 | 0.75000000 | 1.00000000 |
| parent | full - no_clarification | 16 | 1.00000000 | 1.00000000 |
| supplement | directed - plain | 8 | 0.03125000 | 0.15625000 |
| supplement | directed - directed_no_notes | 8 | 0.12500000 | 0.50000000 |

The directed-minus-plain contrast assigns a negotiation instruction bundle. Directed-minus-directed/no-notes tests delivery conditional on that bundle. The design does not estimate a delivery-by-wording interaction or a single linguistic ingredient. Existing context and numeric actions remain possible coordination carriers.

The supplement does not relabel the parent study or old null outcomes. It does not establish spontaneous collusion in a benign deployment. The receipt-gate claim remains bounded to the trusted payment path; observed harm alone is not proof of an agreement.
