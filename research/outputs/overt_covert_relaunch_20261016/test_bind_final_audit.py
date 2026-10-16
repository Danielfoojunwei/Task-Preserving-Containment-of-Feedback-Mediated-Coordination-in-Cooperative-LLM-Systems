"""Synthetic-only tests of pre/post raw-audit byte bindings."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("bind_final_audit", Path(__file__).with_name("bind_final_audit.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "calls" / "one").mkdir(parents=True)
        (self.root / "runs" / "one").mkdir(parents=True)
        (self.root / "calls/one/request.json").write_text('{"x":1}\n')
        (self.root / "calls/one/.call.lock").write_bytes(b"")
        (self.root / "runs/one/end_state.json").write_text('{"x":2}\n')
        self.out = self.root / "independent/final"
        self.install()

    def install(self, mutation="", passed=True, status=0, report_phase="all", report_name="INDEPENDENT_VERIFICATION_ALL.json", verifier_override=None):
        source = "\n".join([
            "import argparse,hashlib,json,pathlib,sys",
            "p=argparse.ArgumentParser();p.add_argument('--root');p.add_argument('--output-dir');p.add_argument('--phase');p.add_argument('--release',action='store_true');a=p.parse_args()",
            "root=pathlib.Path(a.root);out=pathlib.Path(a.output_dir)",
            mutation,
            "v=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()",
            f"report={{'passed':{passed!r},'phase':{report_phase!r},'verifier_sha256':{verifier_override!r} or v,'inventory':{{'calls':3}}}}",
            f"(out/{report_name!r}).write_text(json.dumps(report))",
            f"sys.exit({status!r})", ""])
        (self.root / "independent_verify.py").write_text(source)
        (self.root / "FREEZE.json").write_text(json.dumps({"sha256": {
            "independent_verify.py": hashlib.sha256(source.encode()).hexdigest()}}))

    def audit(self, **kwargs):
        return M.bound_audit(self.root, self.out, **kwargs)

    def reject(self, **kwargs):
        with self.assertRaises(M.BindingError):
            self.audit(**kwargs)
        self.assertFalse((self.out / "SOURCE_BINDINGS.json").exists())

    def test_success_exact_inventory_report_and_timestamp_binding(self):
        result = self.audit()
        manifest = json.loads((self.out / "SOURCE_BINDINGS.json").read_text())
        self.assertTrue(result["passed"])
        self.assertEqual(result["source_artifact_count"], 2)
        self.assertEqual(set(manifest["artifacts"]), {"calls/one/request.json", "runs/one/end_state.json"})
        self.assertEqual(manifest["inventory_excluded_filenames"], [".call.lock", ".budget.lock", ".scheduler.lock"])
        self.assertEqual(manifest["inventory_sha256"], hashlib.sha256(M.canonical(manifest["artifacts"])).hexdigest())
        self.assertEqual(manifest["raw_report"]["sha256"], M.digest(self.out / "INDEPENDENT_VERIFICATION_ALL.json"))
        self.assertEqual(manifest["verifier"]["sha256"], manifest["verifier"]["frozen_sha256"])
        stamps = [manifest[name] for name in ("capture_started_at", "capture_finished_at", "audit_started_at", "audit_finished_at", "confirmed_at")]
        self.assertEqual(stamps, sorted(stamps))
        self.assertEqual((self.out / "SOURCE_BINDINGS.json").stat().st_mode & 0o777, 0o444)

    def test_same_length_mutation_is_detected(self):
        self.install("(root/'calls/one/request.json').write_text('{\"x\":9}\\n')")
        self.reject()

    def test_only_exact_declared_runtime_lock_filenames_excluded(self):
        for name in (".budget.lock", ".scheduler.lock", "unknown.lock", "call.lock", ".call.lock.json"):
            (self.root / "calls/one" / name).write_text("runtime or unknown")
        rows = M.inventory(self.root)
        for name in (".call.lock", ".budget.lock", ".scheduler.lock"):
            self.assertNotIn("calls/one/" + name, rows)
        for name in ("unknown.lock", "call.lock", ".call.lock.json"):
            self.assertIn("calls/one/" + name, rows)

    def test_removed_declared_lock_does_not_invalidate_portable_release(self):
        self.install("(root/'calls/one/.call.lock').unlink()")
        self.assertTrue(self.audit()["passed"])

    def test_matching_source_action_and_endstate_tamper_is_detected(self):
        self.install("(root/'calls/one/request.json').write_text('{\"x\":9}\\n');(root/'runs/one/end_state.json').write_text('{\"x\":9}\\n')")
        self.reject()

    def test_deleted_source_is_detected(self):
        self.install("(root/'calls/one/request.json').unlink()")
        self.reject()

    def test_added_source_is_detected(self):
        self.install("(root/'calls/one/unplanned.json').write_text('{}')")
        self.reject()

    def test_source_symlink_rejected_before_audit(self):
        (self.root / "calls/link.json").symlink_to(self.root / "FREEZE.json")
        self.reject()

    def test_directory_symlink_rejected_before_audit(self):
        (self.root / "runs/link").symlink_to(self.root / "calls", target_is_directory=True)
        self.reject()

    def test_failed_raw_audit_exit_releases_no_manifest(self):
        self.install(status=1)
        self.reject()

    def test_failed_raw_report_releases_no_manifest(self):
        self.install(passed=False)
        self.reject()

    def test_wrong_phase_rejected(self):
        self.install(report_phase="controls")
        self.reject()

    def test_report_wrong_verifier_hash_rejected(self):
        self.install(verifier_override="0"*64)
        self.reject()

    def test_changed_verifier_before_audit_rejected(self):
        with (self.root / "independent_verify.py").open("a") as f:
            f.write("# tampered\n")
        self.reject()

    def test_changed_freeze_during_audit_rejected(self):
        self.install("(root/'FREEZE.json').write_text('{}')")
        self.reject()

    def test_existing_raw_report_cannot_be_overwritten(self):
        self.out.mkdir(parents=True)
        (self.out / "INDEPENDENT_VERIFICATION_ALL.json").write_text("{}")
        self.reject()

    def test_successful_release_cannot_be_overwritten(self):
        self.audit()
        before = M.digest(self.out / "SOURCE_BINDINGS.json")
        with self.assertRaises(M.BindingError):
            self.audit()
        self.assertEqual(M.digest(self.out / "SOURCE_BINDINGS.json"), before)

    def test_continuation_unsuffixed_report_supported(self):
        self.install(report_name="INDEPENDENT_VERIFICATION.json")
        result = self.audit(report_name="INDEPENDENT_VERIFICATION.json", verifier_args=("--release",))
        self.assertTrue(result["passed"])
        self.assertTrue((self.out / "INDEPENDENT_VERIFICATION.json").is_file())

    def test_duplicate_and_nonfinite_json_rejected(self):
        path = self.root / "bad.json"
        for text in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            path.write_text(text)
            with self.assertRaises(M.BindingError):
                M.read_json(path)

    def test_cli_requires_release_before_accessing_root(self):
        result = subprocess.run([sys.executable, str(Path(M.__file__)), "--root", str(self.root / "absent")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("--release is required", result.stderr)


if __name__ == "__main__":
    unittest.main()
