"""Synthetic-only tests and fixtures for the pre-audit inventory validator."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("synthetic_bindings_validator",HERE/"source_bindings.py")
sb=importlib.util.module_from_spec(spec);spec.loader.exec_module(sb)


def synthetic_manifest(root,raw):
    """Create a test-local audit attestation; never use on actual evidence."""
    root=Path(root);raw=Path(raw)
    for name in ("calls","runs"):(root/name).mkdir(exist_ok=True)
    if not any((root/"calls").iterdir()):(root/"calls"/"synthetic_call.json").write_text('{"synthetic_only":true}')
    if not any((root/"runs").iterdir()):(root/"runs"/"synthetic_state.json").write_text('{"synthetic_only":true}')
    verifier=root/"independent_verify.py"
    if not verifier.exists():verifier.write_text("# Synthetic frozen verifier fixture only\n")
    freeze=root/"FREEZE.json"
    if not freeze.exists():freeze.write_text(json.dumps({"sha256":{"independent_verify.py":sb.digest(verifier.read_bytes())}}))
    artifacts=sb.inventory(root);hash_=lambda path:sb.digest(path.read_bytes())
    raw_value=json.loads(raw.read_text());raw_value["verifier_sha256"]=hash_(verifier);raw.write_text(json.dumps(raw_value))
    value={"schema_version":1,"passed":True,"phase":"all","inventory_roots":["calls","runs"],
        "inventory_excluded_filenames":list(sb.EXCLUDED_LOCKS),
        "capture_started_at":"2026-10-16T01:00:00+00:00","capture_finished_at":"2026-10-16T01:00:01+00:00",
        "audit_started_at":"2026-10-16T01:00:02+00:00","audit_finished_at":"2026-10-16T01:00:03+00:00",
        "confirmed_at":"2026-10-16T01:00:04+00:00","artifact_inventory_unchanged":True,
        "captured_before_audit":True,"checked_unchanged_after_audit":True,
        "artifacts":artifacts,"inventory_sha256":sb.digest(sb.canonical(artifacts)),
        "raw_report":{"path":raw.relative_to(root).as_posix(),"sha256":hash_(raw),"passed":True},
        "verifier":{"path":"independent_verify.py","sha256":hash_(verifier),"frozen_sha256":hash_(verifier)},
        "source_freeze_sha256":hash_(freeze)}
    snapshot={k:value[k] for k in ("schema_version","inventory_roots","inventory_excluded_filenames","capture_started_at","capture_finished_at",
        "artifacts","inventory_sha256","source_freeze_sha256")}
    snapshot["verifier_sha256"]=hash_(verifier)
    before=raw.parent/"SOURCE_SNAPSHOT_BEFORE_AUDIT.json";before.write_text(json.dumps(snapshot))
    value["before_snapshot"]={"path":before.relative_to(root).as_posix(),"sha256":hash_(before)}
    value["binding_wrapper_sha256"]=sb.digest(b"Synthetic wrapper fixture only")
    path=raw.parent/"SOURCE_BINDINGS.json";path.write_text(json.dumps(value));return path


class AuditBindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        (self.root/"runs").mkdir();self.action=self.root/"runs"/"action.json"
        self.action.write_text('{"public_report":"original","amount_valid":true}')
        self.raw=self.root/"raw.json";self.raw.write_text('{"passed":true,"phase":"all"}')
        self.path=synthetic_manifest(self.root,self.raw)

    def tearDown(self):self.tmp.cleanup()
    def changed_manifest(self,edit):
        value=json.loads(self.path.read_text());edit(value);self.path.write_text(json.dumps(value))

    def test_passing_attestation_binds_source_bytes_and_frozen_verifier(self):
        source=sb.SourceBindings(self.root,self.raw)
        source.check(self.action);source.verify_unchanged()
        self.assertEqual(source.provenance()["raw_report_sha256"],sb.digest(self.raw.read_bytes()))

    def test_coupled_report_and_end_state_change_rejected_before_first_read(self):
        self.action.write_text('{"public_report":"injected disclosure","amount_valid":true}')
        with self.assertRaisesRegex(ValueError,"pre-audit source inventory"):sb.SourceBindings(self.root,self.raw)

    def test_validity_change_after_constructor_rejected_on_read(self):
        source=sb.SourceBindings(self.root,self.raw)
        self.action.write_text('{"public_report":"original","amount_valid":false}')
        with self.assertRaisesRegex(ValueError,"pre-audit source inventory"):source.check(self.action)

    def test_unread_wire_call_change_still_rejected_at_final_check(self):
        source=sb.SourceBindings(self.root,self.raw)
        (self.root/"calls"/"synthetic_call.json").write_text('{"raw_content":"tampered"}')
        with self.assertRaisesRegex(ValueError,"pre-audit source inventory"):source.verify_unchanged()

    def test_extra_or_missing_artifact_rejected(self):
        extra=self.root/"runs"/"extra.json";extra.write_text('{}')
        with self.assertRaisesRegex(ValueError,"pre-audit source inventory"):sb.SourceBindings(self.root,self.raw)
        extra.unlink();self.action.unlink()
        with self.assertRaisesRegex(ValueError,"missing or escaped"):sb.SourceBindings(self.root,self.raw)

    def test_raw_report_cannot_be_swapped_after_attestation(self):
        self.raw.write_text('{"passed":true,"phase":"all","new":true}')
        with self.assertRaisesRegex(ValueError,"passing raw report"):sb.SourceBindings(self.root,self.raw)

    def test_frozen_verifier_and_freeze_must_match_attestation(self):
        (self.root/"independent_verify.py").write_text("# modified\n")
        with self.assertRaisesRegex(ValueError,"frozen raw verifier"):sb.SourceBindings(self.root,self.raw)

    def test_capture_must_precede_audit_and_confirmation(self):
        self.changed_manifest(lambda m:m.update(capture_finished_at="2026-10-17T01:00:01+00:00"))
        with self.assertRaisesRegex(ValueError,"precede"):sb.SourceBindings(self.root,self.raw)

    def test_pre_post_audit_positive_assertions_are_required(self):
        self.changed_manifest(lambda m:m.update(captured_before_audit=False))
        with self.assertRaisesRegex(ValueError,"passing pre-audit"):sb.SourceBindings(self.root,self.raw)

    def test_inventory_digest_and_manifest_bytes_are_pinned(self):
        source=sb.SourceBindings(self.root,self.raw)
        self.changed_manifest(lambda m:m.update(inventory_sha256="0"*64))
        with self.assertRaisesRegex(ValueError,"provenance changed"):source.verify_unchanged()
        with self.assertRaisesRegex(ValueError,"inventory digest differs"):sb.SourceBindings(self.root,self.raw)

    def test_persisted_before_snapshot_must_match_final_inventory(self):
        before=self.raw.parent/"SOURCE_SNAPSHOT_BEFORE_AUDIT.json"
        value=json.loads(before.read_text());value["capture_started_at"]="2026-10-16T00:00:00+00:00"
        before.write_text(json.dumps(value))
        self.changed_manifest(lambda m:m["before_snapshot"].update(sha256=sb.digest(before.read_bytes())))
        with self.assertRaisesRegex(ValueError,"snapshot differs"):sb.SourceBindings(self.root,self.raw)

    def test_only_exact_declared_runtime_lock_names_are_excluded(self):
        source=sb.SourceBindings(self.root,self.raw)
        for name in sb.EXCLUDED_LOCKS:(self.root/"calls"/name).write_text("Runtime lock")
        source.verify_unchanged()
        (self.root/"calls"/"semantic.lock").write_text("Unknown files remain bound")
        with self.assertRaisesRegex(ValueError,"pre-audit source inventory"):source.verify_unchanged()

    def test_nonregular_extra_file_is_rejected_without_reading_it(self):
        source=sb.SourceBindings(self.root,self.raw)
        os.mkfifo(self.root/"calls"/"extra.pipe")
        with self.assertRaisesRegex(ValueError,"nonregular"):source.verify_unchanged()


if __name__=="__main__":unittest.main()
