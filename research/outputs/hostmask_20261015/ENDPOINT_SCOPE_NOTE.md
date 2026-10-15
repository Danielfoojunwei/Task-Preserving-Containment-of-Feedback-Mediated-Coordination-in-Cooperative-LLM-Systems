# Endpoint scope: client schema validation and bit extraction

This note documents a limitation of the frozen follow-up implementation. It
does not change its source, protocol, recorded primary endpoint or responses.

The runner's `field_bit` examines the decoded field independently of the frozen
domain parser. A checksum outside the domain range, for example, can invalidate
the accepted host action without erasing a valid decoded bit from the primary
score. The offline certificate checks that separation.

However, the reused strict API client sets `parsed_action={}` when **any client
schema** constraint fails. A hypothetical strict JSON reply with a valid
`decoded_bit` but a string checksum or invalid schedule type can therefore lose
its decoded field before the runner sees it. This means the frozen implementation
is field-independent with respect to downstream domain validity, but not with
respect to every possible upstream client-schema violation. The protocol's broad
wording about all other task/schema failures must be read with this qualification.
Malformed JSON, duplicate keys and nonfinite values are rejected separately.

An independent reviewer raised this edge case around the launch handoff. The
root had already frozen and launched the follow-up; no proposed correction was
applied. All six frozen hashes remained unchanged. The study was completed and
analyzed with that exact implementation.

Post-completion checks found:

- **368/368** source/receiver calls were client-schema-valid.
- **320/320** receiver actions were domain-valid.
- Strictly reparsing actual raw receiver JSON and extracting only the bit gave
  **zero differences** from the frozen client-parsed bit used by the primary.
- **Zero observed records** are affected by the hypothetical clearing behavior.

Thus no alternative bit extraction changes this dataset's primary observations.
This fact does not remove the implementation limitation for future datasets.
A future protocol could predeclare independent strict-JSON field extraction,
while retaining schema/domain rejection for accepted actions. That would be a
new version, not a silent repair of this frozen study.

One certificate wording detail is also qualified here: payload-only and marginal
guards produce **uniform** individual host-mask fields. The full guard produces
**fixed**, bit-independent fields. All have individual TV zero; the full guard
does not make its fixed fields uniform. The executable certificate checks the
correct TV/equality statements; its broad prose about field uniformity should
not be interpreted as a claim of a uniform full-guard output.

These checks are retained in
[HOSTMASK_EXTRA_SUMMARY.json](HOSTMASK_EXTRA_SUMMARY.json), with independent final
integrity validation supplied by the study auditor. No API calls were made to
produce this note.
