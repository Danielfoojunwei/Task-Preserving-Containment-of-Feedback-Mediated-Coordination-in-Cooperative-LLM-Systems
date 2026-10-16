"""Synthetic-only packaging/offline tests; never read actual study outputs."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile
from test_source_bindings import synthetic_manifest

HERE=Path(__file__).resolve().parent
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
p=module("synthetic_package_tools","package_evidence.py")
v=module("synthetic_offline_tools","verify_offline.py")


MAIN_RAW_SCRIPT='''import argparse,json,socket
from pathlib import Path
q=argparse.ArgumentParser();q.add_argument('--root',type=Path);q.add_argument('--phase');q.add_argument('--release',action='store_true');q.add_argument('--output-dir',type=Path);a=q.parse_args()
assert a.release
try:socket.getaddrinfo('invalid.example',443)
except RuntimeError:blocked=True
else:raise AssertionError('network guard not installed')
d=json.loads((a.root/'independent/final/INDEPENDENT_VERIFICATION_ALL.json').read_text())
d.update(root=str(a.root),generated_at='fresh',network_guard_observed=blocked)
a.output_dir.mkdir(parents=True);(a.output_dir/'INDEPENDENT_VERIFICATION_ALL.json').write_text(json.dumps(d))
'''
MAIN_ANALYSIS_SCRIPT='''import argparse,json,os
from pathlib import Path
q=argparse.ArgumentParser();q.add_argument('--root',type=Path);q.add_argument('--sealed-reviews');q.add_argument('--release',action='store_true');q.add_argument('--output',type=Path);a=q.parse_args()
assert a.release and not os.getenv('OPENROUTER_API_KEY')
d=json.loads((a.root/'ANALYSIS.json').read_text());d['review_release']['path']=a.sealed_reviews
a.output.write_text(json.dumps(d))
'''
CONT_RAW_SCRIPT='''import argparse,json
from pathlib import Path
q=argparse.ArgumentParser();q.add_argument('--root',type=Path);q.add_argument('--release',action='store_true');q.add_argument('--output-dir',type=Path);a=q.parse_args();assert a.release
d=json.loads((a.root/'independent/final/INDEPENDENT_VERIFICATION.json').read_text());d.update(root=str(a.root),generated_at='fresh')
a.output_dir.mkdir(parents=True);(a.output_dir/'INDEPENDENT_VERIFICATION.json').write_text(json.dumps(d))
'''
CONT_ANALYSIS_SCRIPT='''import argparse,json,hashlib
from pathlib import Path
q=argparse.ArgumentParser();q.add_argument('--verification',type=Path);q.add_argument('--release',action='store_true');q.add_argument('--output',type=Path);a=q.parse_args();assert a.release
d=json.loads(Path(__file__).with_name('ANALYSIS.json').read_text());d['independent_verification_sha256']=hashlib.sha256(a.verification.read_bytes()).hexdigest()
a.output.write_text(json.dumps(d))
'''
PRIMARY_SCRIPT='''import argparse,json,hashlib
from pathlib import Path
q=argparse.ArgumentParser();q.add_argument('--root',type=Path);q.add_argument('--verified-rounds',type=Path);q.add_argument('--sealed-reviews',type=Path);q.add_argument('--analysis',type=Path);q.add_argument('--output',type=Path);q.add_argument('--release',action='store_true');a=q.parse_args();assert a.release
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
d={'passed':True,'failures':[],'generated_at':'fresh','source_hashes':{'verifier':sha(Path(__file__)),'plan':sha(a.root/'plan.json'),'raw_audit':sha(a.verified_rounds),'sealed_reviews':sha(a.sealed_reviews),'analysis':sha(a.analysis),'source_binding_validator':sha(a.root.parent/'overt_covert_release_20261016/source_bindings.py')}}
a.output.parent.mkdir(parents=True);a.output.write_text(json.dumps(d))
raise SystemExit(0 if d['passed'] else 1)
'''


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/"repo";self.root.mkdir()
        for name in p.TREES:
            folder=self.root/p.REL/name;folder.mkdir(parents=True);(folder/"README.md").write_text("Synthetic fixture only\n")
        self.validator=self.root/p.REL/"overt_covert_release_20261016/source_bindings.py"
        self.validator.write_bytes((HERE/"source_bindings.py").read_bytes())
        self.main=self.root/p.REL/p.MAIN
        self.write(self.main/"independent_verify.py",MAIN_RAW_SCRIPT)
        self.write(self.main/"analyze.py",MAIN_ANALYSIS_SCRIPT)
        self.write(self.main/"test_dummy.py","import unittest\nclass Dummy(unittest.TestCase):\n def test_offline(self): self.assertTrue(True)\n")
        self.reviews=self.main/"manual_reviews/SEALED_PRIMARY_REVIEWS.json"
        self.json(self.reviews,{"worlds":[],"synthetic_only":True})
        self.raw=self.main/"independent/final/INDEPENDENT_VERIFICATION_ALL.json"
        self.json(self.raw,{"passed":True,"phase":"all","root":"/historical/workspace","generated_at":"old",
            "network_guard_observed":True,"inventory":{"verified_calls":6608},"calls":[],"outcome":17})
        self.json(self.main/"ANALYSIS.json",{"inference_eligible":True,"review_release":{"sha256":p.sha(self.reviews),"path":"/historical/reviews.json"},"observed":17})
        parent=self.root/p.REL/"required_parent";parent.mkdir()
        (parent/"helper.py").write_text("# pinned parent helper\n")
        self.json(parent/"FREEZE.json",{"sha256":{"helper.py":p.sha(parent/"helper.py")}})
        self.json(self.main/"FREEZE.json",{"sha256":{"../required_parent/FREEZE.json":p.sha(parent/"FREEZE.json"),
            "independent_verify.py":p.sha(self.main/"independent_verify.py"),"analyze.py":p.sha(self.main/"analyze.py")}})
        synthetic_manifest(self.main,self.raw)
        self.archive=Path(self.tmp.name)/"evidence.zip"

    def tearDown(self):self.tmp.cleanup()
    def write(self,path,text):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    def json(self,path,obj):self.write(path,json.dumps(obj))
    def package(self):return p.build(self.archive,self.root)
    def extract(self):
        folder=Path(self.tmp.name)/"extracted"
        with zipfile.ZipFile(self.archive) as z:z.extractall(folder)
        return folder/p.PREFIX

    def add_continuation(self):
        folder=self.root/p.REL/p.CONTINUATION;folder.mkdir()
        self.write(folder/"independent_verify.py",CONT_RAW_SCRIPT)
        self.write(folder/"analyze.py",CONT_ANALYSIS_SCRIPT)
        self.json(folder/"continuations_completion.json",{"complete":True})
        raw=folder/"independent/final/INDEPENDENT_VERIFICATION.json"
        self.json(raw,{"passed":True,"phase":"all","root":"/old/continuation","generated_at":"old","outcome":9})
        synthetic_manifest(folder,raw)
        self.json(folder/"ANALYSIS.json",{"complete":True,"outcome":9,"independent_verification_sha256":p.sha(raw)})

    def add_primary(self,fresh_pass=True):
        source=PRIMARY_SCRIPT if fresh_pass else PRIMARY_SCRIPT.replace("'passed':True","'passed':False")
        self.write(self.main/"independent_primary.py",source)
        self.json(self.main/"plan.json",{"synthetic_only":True})
        report={"passed":True,"failures":[],"generated_at":"old","source_hashes":{
            "verifier":p.sha(self.main/"independent_primary.py"),"plan":p.sha(self.main/"plan.json"),
            "raw_audit":p.sha(self.raw),"sealed_reviews":p.sha(self.reviews),"analysis":p.sha(self.main/"ANALYSIS.json"),
            "source_binding_validator":p.sha(self.validator)}}
        path=self.main/"independent/primary/INDEPENDENT_PRIMARY_VERIFICATION.json"
        self.json(path,report);return path

    def test_recursive_freeze_closure_copies_required_parent_not_entire_old_cohort(self):
        unrelated=self.root/p.REL/"required_parent/unrelated_private_research.json"
        unrelated.write_text('{"unused":true}')
        files,refs,_=p.collect(self.root)
        self.assertIn(self.root/p.REL/"required_parent/helper.py",files)
        self.assertNotIn(unrelated,files)
        self.assertEqual(len(refs),4)

    def test_excludes_environment_keys_caches_locks_archives_and_git(self):
        for name in (".env","test.key","notes.zip","x.lock","__pycache__/x.pyc",".git/config"):
            self.write(self.main/name,"excluded synthetic file")
        self.package();bundle=self.extract();manifest=v.verify_manifest(bundle)
        names=list(manifest["files"])
        self.assertFalse(any(x.endswith((".env",".key",".zip",".lock",".pyc",".git/config")) for x in names))

    def test_optional_docs_ci_and_future_presentation_copied_when_present(self):
        for name in p.OPTIONAL_FILES:self.write(self.root/name,"Synthetic updated documentation\n")
        presentation=self.root/"presentations/overt_covert_20261016"
        self.write(presentation/"SLIDES.md","Synthetic slide notes\n")
        self.write(presentation/"index.html","<p>Synthetic slides</p>")
        self.write(presentation/"nested.zip","Excluded nested archive")
        self.package();bundle=self.extract();manifest=v.verify_manifest(bundle)
        for name in p.OPTIONAL_FILES:self.assertIn(name,manifest["files"])
        self.assertIn("presentations/overt_covert_20261016/SLIDES.md",manifest["files"])
        self.assertIn("presentations/overt_covert_20261016/index.html",manifest["files"])
        self.assertNotIn("presentations/overt_covert_20261016/nested.zip",manifest["files"])
        text=(bundle/"README_REPRODUCE.md").read_text()
        self.assertIn("reciprocity-evidence-20261016-final.zip",text)
        self.assertIn("not silently included",text)
        self.assertIn("CPython 3.12.14",text)
        self.assertNotIn("Python 3.11+",text)
        self.assertIn("--allow-other-python-3-12-patch",text)

    def test_missing_optional_documents_and_presentation_are_allowed(self):
        files,_,_=p.collect(self.root)
        self.assertTrue(files)
        self.assertFalse(any(self.root/name in files for name in p.OPTIONAL_FILES))

    def test_frozen_parent_changes_prevent_archive_creation(self):
        (self.root/p.REL/"required_parent/helper.py").write_text("# modified\n")
        with self.assertRaisesRegex(ValueError,"frozen dependency bytes changed"):self.package()
        self.assertFalse(self.archive.exists())

    def test_symlink_parent_reference_not_silently_dereferenced(self):
        parent=self.root/p.REL/"required_parent"
        target=parent/"helper.py";target.unlink();target.symlink_to(parent/"FREEZE.json")
        with self.assertRaisesRegex(ValueError,"symlink"):self.package()

    def test_key_shaped_literal_aborts_without_archive_or_partial(self):
        self.write(self.main/"unfrozen_log.txt","sk-or-v1-"+"a"*64)
        with self.assertRaisesRegex(ValueError,"credential-shaped"):self.package()
        self.assertFalse(self.archive.exists())
        self.assertEqual(list(self.archive.parent.glob("*.partial")),[])

    def test_archive_overwrite_refused(self):
        self.package()
        with self.assertRaises(FileExistsError):self.package()

    def test_manifest_detects_changed_extracted_bytes(self):
        self.package();bundle=self.extract()
        (bundle/p.REL/"required_parent/helper.py").write_text("# tampered")
        with self.assertRaisesRegex(ValueError,"byte verification failed"):v.verify_manifest(bundle)

    def test_actual_main_suffix_and_no_runner_commands(self):
        self.package();bundle=self.extract();manifest=v.verify_manifest(bundle)
        commands=v.command_plan(bundle,Path(self.tmp.name)/"output",manifest)
        raw=next(c for n,c in commands if n=="main_raw")
        self.assertIn("--phase",raw);self.assertIn("all",raw)
        self.assertTrue(manifest["main_verification"].endswith("INDEPENDENT_VERIFICATION_ALL.json"))
        self.assertFalse(any("run_study.py" in argument for _,c in commands for argument in c))

    def test_full_synthetic_reproduction_blocks_network_and_removes_key(self):
        self.package();bundle=self.extract()
        with patch.dict(os.environ,{"OPENROUTER_API_KEY":"unit-only-key-material"}):
            report=v.reproduce(bundle,Path(self.tmp.name)/"reproduction")
        self.assertTrue(report["passed"])
        self.assertEqual([c["kind"] for c in report["comparisons"]],["main_raw","main_analysis"])
        self.assertIn("OPENROUTER_API_KEY",report["credential_variable_names_removed"])
        self.assertTrue(report["network_blocked"])
        self.assertFalse(report["runners_launched"])
        self.assertEqual(len(report["archived_source_bindings"]),1)
        self.assertTrue(report["runtime"]["exact_runtime_match"])
        self.assertFalse(report["runtime"]["numeric_comparisons_relaxed"])
        self.assertEqual(json.loads((Path(report["output_dir"])/"OFFLINE_RUNTIME_CHECK.json").read_text()),report["runtime"])

    def test_completed_continuation_reproduces_after_raw_provenance_comparison(self):
        self.add_continuation();self.package();bundle=self.extract()
        report=v.reproduce(bundle,Path(self.tmp.name)/"reproduction",skip_unit_tests=True)
        self.assertTrue(report["passed"])
        self.assertEqual([c["kind"] for c in report["comparisons"]],
                         ["main_raw","main_analysis","continuation_raw","continuation_analysis"])
        self.assertEqual(report["comparisons"][-1]["ignored_fields"],["independent_verification_sha256"])

    def test_optional_independent_primary_runs_on_fresh_raw_and_analysis(self):
        self.add_primary();self.package();bundle=self.extract()
        report=v.reproduce(bundle,Path(self.tmp.name)/"reproduction",skip_unit_tests=True)
        self.assertTrue(report["passed"])
        self.assertEqual([s["name"] for s in report["steps"]],["main_raw","main_analysis","main_primary"])
        checks=report["independent_primary_checks"]
        self.assertEqual([c["scope"] for c in checks],["archived","freshly reproduced"])
        self.assertTrue(all(c["passed"] for c in checks))
        self.assertNotEqual(checks[0]["source_hashes"]["raw_audit"],checks[1]["source_hashes"]["raw_audit"])
        expected_keys={"verifier","plan","raw_audit","sealed_reviews","analysis","source_binding_validator"}
        for check in checks:
            self.assertEqual(set(check["source_hashes"]),expected_keys)
            self.assertEqual(check["source_hashes"]["source_binding_validator"],p.sha(self.validator))

    def test_primary_source_hash_mismatch_refuses_package(self):
        path=self.add_primary();d=json.loads(path.read_text());d["source_hashes"]["analysis"]="0"*64
        self.json(path,d)
        with self.assertRaisesRegex(ValueError,"primary source hashes"):self.package()
        self.assertFalse(self.archive.exists())

    def change_primary_hashes(self,change):
        path=self.add_primary();report=json.loads(path.read_text());change(report["source_hashes"])
        self.json(path,report);return path

    def check_primary(self,path):
        return v.validate_primary_check(path,self.main/"independent_primary.py",self.main/"plan.json",
            self.raw,self.reviews,self.main/"ANALYSIS.json",self.validator)

    def test_primary_missing_validator_hash_refuses_package(self):
        self.change_primary_hashes(lambda hashes:hashes.pop("source_binding_validator"))
        with self.assertRaisesRegex(ValueError,"primary source hashes"):self.package()
        self.assertFalse(self.archive.exists())

    def test_primary_wrong_validator_hash_refuses_package(self):
        self.change_primary_hashes(lambda hashes:hashes.update(source_binding_validator="0"*64))
        with self.assertRaisesRegex(ValueError,"primary source hashes"):self.package()
        self.assertFalse(self.archive.exists())

    def test_primary_extra_hash_is_not_silently_ignored_by_package(self):
        self.change_primary_hashes(lambda hashes:hashes.update(unexpected="0"*64))
        with self.assertRaisesRegex(ValueError,"primary source hashes"):self.package()
        self.assertFalse(self.archive.exists())

    def test_offline_primary_missing_validator_hash_rejected(self):
        path=self.change_primary_hashes(lambda hashes:hashes.pop("source_binding_validator"))
        with self.assertRaisesRegex(ValueError,"input hashes differ"):self.check_primary(path)

    def test_offline_primary_wrong_validator_hash_rejected(self):
        path=self.change_primary_hashes(lambda hashes:hashes.update(source_binding_validator="0"*64))
        with self.assertRaisesRegex(ValueError,"input hashes differ"):self.check_primary(path)

    def test_offline_primary_extra_hash_is_not_silently_ignored(self):
        path=self.change_primary_hashes(lambda hashes:hashes.update(unexpected="0"*64))
        with self.assertRaisesRegex(ValueError,"input hashes differ"):self.check_primary(path)

    def test_changed_validator_bytes_rejected_by_both_contracts(self):
        path=self.add_primary();self.validator.write_bytes(self.validator.read_bytes()+b"\n# changed after primary check\n")
        with self.assertRaisesRegex(ValueError,"primary source hashes"):self.package()
        self.assertFalse(self.archive.exists())
        with self.assertRaisesRegex(ValueError,"input hashes differ"):self.check_primary(path)

    def test_new_primary_failure_makes_offline_reproduction_fail(self):
        self.add_primary(fresh_pass=False);self.package();bundle=self.extract()
        report=v.reproduce(bundle,Path(self.tmp.name)/"reproduction",skip_unit_tests=True)
        self.assertFalse(report["passed"])
        self.assertEqual(report["steps"][-1]["name"],"main_primary")
        self.assertEqual(report["steps"][-1]["returncode"],1)

    def test_outputs_inside_bundle_refused(self):
        self.package();bundle=self.extract()
        with self.assertRaises(ValueError):v.reproduce(bundle,bundle/"new_outputs")

    def test_packaging_rejects_changed_source_after_passing_audit(self):
        (self.main/"calls/synthetic_call.json").write_text('{"post_audit_change":true}')
        with self.assertRaisesRegex(ValueError,"pre-audit source inventory"):self.package()
        self.assertFalse(self.archive.exists())

    def test_offline_check_rejects_missing_archived_source_binding(self):
        self.package();bundle=self.extract()
        path=bundle/"SOURCE_MANIFEST.json";manifest=json.loads(path.read_text());manifest.pop("main_source_bindings")
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError,"pre-audit source bindings"):v.verify_manifest(bundle)


class ComparisonAndPaths(unittest.TestCase):
    def test_original_runtime_is_explicitly_recorded(self):
        with patch.object(v.sys,"version_info",(3,12,14,"final",0)),patch.object(v.sys,"implementation",SimpleNamespace(name="cpython")):
            result=v.runtime_check()
        self.assertTrue(result["passed"])
        self.assertTrue(result["exact_runtime_match"])
        self.assertEqual(result["required_python_version"],"3.12.14")
        self.assertFalse(result["other_3_12_patch_explicitly_allowed"])

    def test_only_explicit_final_cpython_3_12_patch_override_is_allowed(self):
        with patch.object(v.sys,"implementation",SimpleNamespace(name="cpython")):
            with patch.object(v.sys,"version_info",(3,12,13,"final",0)):
                self.assertFalse(v.runtime_check()["passed"])
                result=v.runtime_check(True)
                self.assertTrue(result["passed"])
                self.assertFalse(result["exact_runtime_match"])
                self.assertTrue(result["other_3_12_patch_explicitly_allowed"])
                self.assertFalse(result["numeric_comparisons_relaxed"])
            for version in ((3,11,14,"final",0),(3,13,0,"final",0),(3,12,14,"alpha",1)):
                with patch.object(v.sys,"version_info",version):
                    self.assertFalse(v.runtime_check(True)["passed"])
        with patch.object(v.sys,"version_info",(3,12,14,"final",0)),patch.object(v.sys,"implementation",SimpleNamespace(name="pypy")):
            self.assertFalse(v.runtime_check(True)["passed"])

    def test_runtime_mismatch_is_recorded_before_evidence_reads_or_processes(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/"output"
            with patch.object(v.sys,"version_info",(3,11,14,"final",0)),patch.object(v,"verify_manifest") as manifest,patch.object(v.subprocess,"run") as process:
                with self.assertRaisesRegex(ValueError,"requires CPython 3.12.14; observed"):
                    v.reproduce(Path(tmp)/"unopened_evidence",output)
                manifest.assert_not_called();process.assert_not_called()
            check=json.loads((output/"OFFLINE_RUNTIME_CHECK.json").read_text())
            self.assertFalse(check["passed"])
            self.assertEqual(check["observed_python_version"],"3.11.14")

    def test_runtime_override_does_not_relax_small_numeric_differences(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b=Path(tmp)/"a.json",Path(tmp)/"b.json"
            a.write_text(json.dumps({"bootstrap":0.123456789012345}))
            b.write_text(json.dumps({"bootstrap":0.123456789012346}))
            with self.assertRaisesRegex(ValueError,"substantive JSON differs"):
                v.compare_json(a,b,"main_analysis")

    def test_only_declared_raw_path_timestamp_fields_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,bpath=Path(tmp)/"a.json",Path(tmp)/"b.json"
            a.write_text(json.dumps({"root":"/old","generated_at":"old","scores":[1,2],"calls":["id"]}))
            bpath.write_text(json.dumps({"root":"/new","generated_at":"new","scores":[1,2],"calls":["id"]}))
            self.assertTrue(v.compare_json(a,bpath,"main_raw")["substantive_equal"])
            d=json.loads(bpath.read_text());d["scores"]=[1,3];bpath.write_text(json.dumps(d))
            with self.assertRaises(ValueError):v.compare_json(a,bpath,"main_raw")

    def test_absolute_and_traversal_manifest_paths_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("/etc/passwd","../outside.json"):
                with self.assertRaises(ValueError):v.checked_path(Path(tmp),name)

    def test_commands_require_release_before_any_actual_reads(self):
        with self.assertRaises(SystemExit):p.main(["--out","/does-not-exist.zip"])
        with self.assertRaises(SystemExit):v.main(["--bundle-root","/does-not-exist"])


if __name__=="__main__":unittest.main()
