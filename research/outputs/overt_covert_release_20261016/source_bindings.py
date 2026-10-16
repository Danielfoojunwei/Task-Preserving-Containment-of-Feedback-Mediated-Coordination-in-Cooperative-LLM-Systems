"""Validate a pre-audit calls/runs inventory against its passing frozen audit.

This supplemental provenance check does not replace the frozen raw-wire parser.
Import opens no study data. Inventory hashes are local evidence, not external
attestation of a timestamp or public preregistration.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat

EXCLUDED_LOCKS=(".call.lock",".budget.lock",".scheduler.lock")

def digest(blob):return hashlib.sha256(blob).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def read_json(path):
    def pairs(items):
        value={}
        for key,item in items:
            if key in value:raise ValueError("duplicate source-binding JSON key")
            value[key]=item
        return value
    def reject(value):raise ValueError("nonfinite source-binding JSON value")
    return json.loads(Path(path).read_bytes(),object_pairs_hook=pairs,parse_constant=reject)


def safe_path(root,relative):
    part=PurePosixPath(relative)
    if part.is_absolute() or not part.parts or any(p in (".","..") for p in part.parts):
        raise ValueError("invalid source-binding artifact path")
    root=Path(root).resolve();path=root.joinpath(*part.parts)
    if not path.resolve().is_relative_to(root) or not path.is_file():
        raise ValueError("missing or escaped source-binding artifact: "+relative)
    if any(p.is_symlink() for p in (path,*path.parents) if p.is_relative_to(root)):
        raise ValueError("symlink source-binding artifact")
    return path


def inventory(root):
    result={};root=Path(root).resolve()
    for name in ("calls","runs"):
        folder=root/name
        if not folder.is_dir() or folder.is_symlink():raise ValueError("missing calls/runs source inventory root")
        for path in sorted(folder.rglob("*")):
            if path.is_symlink():raise ValueError("symlink in calls/runs source inventory")
            if path.name in EXCLUDED_LOCKS:continue
            before=path.lstat()
            if stat.S_ISDIR(before.st_mode):continue
            if not stat.S_ISREG(before.st_mode):raise ValueError("nonregular calls/runs source artifact")
            blob=path.read_bytes();after=path.lstat()
            if (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns):
                raise ValueError("source artifact changed while checking inventory")
            result[path.relative_to(root).as_posix()]={"sha256":digest(blob),"bytes":len(blob)}
    if not result:raise ValueError("empty audited source inventory")
    return result


class SourceBindings:
    def __init__(self,root,raw_report,manifest=None):
        self.root=Path(root).resolve();self.raw_report=Path(raw_report).resolve()
        self.path=Path(manifest or self.raw_report.parent/"SOURCE_BINDINGS.json").resolve()
        if not self.path.is_relative_to(self.root):raise ValueError("source-binding manifest must remain inside its study")
        self.manifest=read_json(self.path);m=self.manifest
        if (m.get("schema_version")!=1 or m.get("passed") is not True or m.get("phase")!="all"
                or m.get("inventory_roots")!=["calls","runs"] or m.get("artifact_inventory_unchanged") is not True
                or m.get("inventory_excluded_filenames")!=list(EXCLUDED_LOCKS)
                or m.get("captured_before_audit") is not True or m.get("checked_unchanged_after_audit") is not True):
            raise ValueError("passing pre-audit source bindings are required")
        times=[]
        for key in ("capture_started_at","capture_finished_at","audit_started_at","audit_finished_at","confirmed_at"):
            try:
                value=m[key]
                if type(value) is not str:raise ValueError()
                stamp=datetime.fromisoformat(value.replace("Z","+00:00"))
            except (KeyError,TypeError,ValueError):raise ValueError("invalid source-binding audit chronology") from None
            if stamp.utcoffset()!=timezone.utc.utcoffset(stamp):raise ValueError("source-binding timestamps must be UTC")
            times.append(stamp)
        if times!=sorted(times):raise ValueError("source inventory must precede its audit and final confirmation")
        artifacts=m.get("artifacts")
        if type(artifacts) is not dict or not artifacts or digest(canonical(artifacts))!=m.get("inventory_sha256"):
            raise ValueError("source-binding inventory digest differs")
        for name,entry in artifacts.items():
            safe_path(self.root,name)
            if not PurePosixPath(name).parts or PurePosixPath(name).parts[0] not in ("calls","runs"):
                raise ValueError("unexpected root in audited source inventory")
            if (type(entry) is not dict or set(entry)!={"sha256","bytes"} or type(entry["bytes"]) is not int
                    or entry["bytes"]<0 or type(entry["sha256"]) is not str or len(entry["sha256"])!=64):
                raise ValueError("invalid audited source inventory entry")
        report=m.get("raw_report",{});verifier=m.get("verifier",{})
        if safe_path(self.root,report["path"])!=self.raw_report or report.get("passed") is not True:
            raise ValueError("source bindings refer to another raw report")
        if verifier.get("path")!="independent_verify.py":raise ValueError("unexpected frozen raw verifier path")
        self.verifier=safe_path(self.root,verifier["path"]);self.freeze=self.root/"FREEZE.json"
        freeze=read_json(self.freeze)
        expected=freeze.get("sha256",{}).get("independent_verify.py")
        if (not expected or verifier.get("sha256")!=expected or verifier.get("frozen_sha256")!=expected
                or digest(self.verifier.read_bytes())!=expected):
            raise ValueError("source bindings do not bind the frozen raw verifier")
        if digest(self.freeze.read_bytes())!=m.get("source_freeze_sha256"):
            raise ValueError("source-binding freeze bytes changed")
        raw=read_json(self.raw_report)
        if (digest(self.raw_report.read_bytes())!=report.get("sha256") or raw.get("passed") is not True or raw.get("phase")!="all"):
            raise ValueError("source bindings do not bind their passing raw report")
        if raw.get("verifier_sha256")!=expected:raise ValueError("raw report does not bind the frozen verifier")
        before=m.get("before_snapshot",{});self.before=safe_path(self.root,before["path"])
        snapshot=read_json(self.before)
        if digest(self.before.read_bytes())!=before.get("sha256"):
            raise ValueError("pre-audit snapshot bytes changed")
        expected_snapshot={"schema_version":1,"inventory_roots":["calls","runs"],
            "inventory_excluded_filenames":list(EXCLUDED_LOCKS),
            "capture_started_at":m["capture_started_at"],"capture_finished_at":m["capture_finished_at"],
            "artifacts":artifacts,"inventory_sha256":m["inventory_sha256"],
            "source_freeze_sha256":m["source_freeze_sha256"],"verifier_sha256":expected}
        if snapshot!=expected_snapshot:raise ValueError("pre-audit snapshot differs from final source binding")
        self.pinned={self.path:digest(self.path.read_bytes()),self.raw_report:report["sha256"],
            self.verifier:expected,self.freeze:m["source_freeze_sha256"],self.before:before["sha256"]}
        self.verify_unchanged()

    def check(self,path,blob=None):
        path=Path(path).resolve()
        if not path.is_relative_to(self.root):return
        relative=path.relative_to(self.root).as_posix()
        if not relative.startswith(("calls/","runs/")):return
        safe_path(self.root,relative)
        content=path.read_bytes() if blob is None else blob
        if self.manifest["artifacts"].get(relative)!={"sha256":digest(content),"bytes":len(content)}:
            raise ValueError("artifact differs from pre-audit source inventory: "+relative)

    def verify_unchanged(self):
        if any(digest(path.read_bytes())!=expected for path,expected in self.pinned.items()):
            raise ValueError("source-binding audit provenance changed")
        if inventory(self.root)!=self.manifest["artifacts"]:
            raise ValueError("calls/runs artifacts differ from pre-audit source inventory")

    def provenance(self):
        return {"path":self.path.relative_to(self.root).as_posix(),"sha256":self.pinned[self.path],
            "inventory_sha256":self.manifest["inventory_sha256"],
            "raw_report_sha256":self.pinned[self.raw_report],"frozen_verifier_sha256":self.pinned[self.verifier]}
