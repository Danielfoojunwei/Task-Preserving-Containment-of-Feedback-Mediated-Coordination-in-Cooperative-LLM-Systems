# Secondary export guard correction, retained separately

The frozen `formation/secondary_execution.py` rejected the released analysis
before exporting any outcome-aware review packets. The plan uses `rounds: 3`
as an integer count. The primary analyzer intentionally replaces that field with
`rounds: [...]`, containing the three detailed records. The secondary helper's
factor comparison compared those two different representations directly and
raised `released analysis session factors differ from frozen plan`.

This is an implementation defect in the secondary reporting guard. It is not an
experimental observation, a model refusal, or evidence about collusion. The
primary analysis and the separately reconstructed primary comparisons had
already been released. The original frozen sources and all recorded API
requests, replies, assignments, equations, rubrics, primary labels, outcomes and
tests remain unchanged.

The new `release/secondary_execution_v2.py` is a separately retained copy of the
frozen helper with these explicit changes:

1. Resolve the imported analyzer and study defaults through the sibling
   `formation` directory.
2. Compare each fixed plan factor except the overloaded `rounds` key. Require
   the expected plan count to be exactly integer 3 and the analysis field to be
   exactly three ordered dictionary records numbered 1, 2 and 3. Missing,
   repeated, reordered, extra or incorrectly typed records are rejected.
3. Use the actual archived verifier directory `independent/all` as the default,
   matching the explicit path previously required by the frozen helper.
4. Include the v2 helper digest, frozen helper digest and narrow correction
   scope in every exported packet's source bindings. Existing raw/source,
   primary-seal, complete-world coverage, financial reconstruction and literal
   evidence checks remain in force.

The tier logic, annotation validation, mathematical predicates and quote/delivery
validation functions are byte-identical to the frozen helper. Eight regression
tests reproduce the original failure using the actual analysis-schema shape,
confirm the corrected guard accepts that shape, reject incorrect factors and
round structures, preserve source-link/coverage rejection, and check unchanged
tier and annotation function source.

The earlier secondary synthetic tests exercised individual predicates and
packet reconstruction but did not exercise the complete guard with the primary
analyzer's overloaded `rounds` field. This new regression closes that gap. It
does not justify describing all possible implementation errors as eliminated.

The corrected exporter completed all **36 heldout worlds and 108 rounds** after
the primary seal and numerical release. It independently reconstructed every
exported financial row from the raw wire records before writing the packets. No
new API calls were made. Outcome-aware reviewers use the same planned rubric;
this correction does not introduce a new hypothesis test or change a label.

Provenance at export:

- Frozen helper SHA256:
  `404329096f8146230f2e17d57f67d4d61368d720dedbe2dd8f8e7f4bd4b74f02`
- V2 helper SHA256:
  `6a576a731eb94d482da90b51c510783710fc884c97e6353eeaf6c735d4810819`
- Primary seal SHA256:
  `dc1991d486f4eabf27ca816d81e8b097116c2745df70e25b6930ed746d13166c`
- Released primary analysis SHA256:
  `076c69cde9e032aae138ae6bfa1c3fb33dabf9cfe7aafb5ffbb9b8fb8472522a`
- Complete independent raw verification SHA256:
  `4add7701f34d875fbf6e67eeee35c96879264503aa51bd3ad63c9f448cc8078d`

Run from the repository root:

```sh
python -m unittest discover -s research/outputs/covert_extension_20261016/release -p test_secondary_v2.py
python research/outputs/covert_extension_20261016/release/secondary_execution_v2.py --prepare --release
python research/outputs/covert_extension_20261016/release/secondary_execution_v2.py --merge --release
```

Preparation is idempotent only when the existing packet bytes match exactly.
The merger requires every planned secondary review and refuses to overwrite a
released result. Preserve this correction note alongside the frozen sources and
new helper so the reporting chronology remains inspectable.
