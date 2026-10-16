#!/usr/bin/env python3
"""One bounded, prospectively frozen authentication/concurrency diagnostic."""
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import threading

HERE = Path(__file__).resolve().parent
CLIENT = HERE.parent / "controlplane_20261015" / "api_client.py"


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def save(path, value):
    data = canonical(value)
    if path.exists():
        if path.read_bytes() != data:
            raise RuntimeError("Immutable diagnostic artifact differs")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(data)
    return value


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    if list((HERE / "calls").glob("**/attempt_*.started.json")):
        raise RuntimeError("Cannot create a prospective freeze after dispatch")
    plan = {"purpose": "Neutral transport authentication diagnostic, never behavioral evidence",
        "authorization": "Root authorized exactly 12 neutral requests after failed study launch; no main experiment authorization",
        "model": "openai/gpt-4.1", "temperature": .7, "max_tokens": 32,
        "messages": [{"role": "system", "content": "Return only a JSON object."},
                     {"role": "user", "content": "Return {\"ok\":true}."}],
        "max_attempts": 1, "max_workers": 3, "cap_usd": .25, "per_started_call_reserve_usd": .02,
        "max_reserved_usd": .24, "max_calls": 12,
        "phases": [{"name": "sequential", "workers": 1,
                    "call_ids": [f"sequential_{i:02d}" for i in range(1, 7)]},
                   {"name": "concurrent", "workers": 3,
                    "call_ids": [f"concurrent_{i:02d}" for i in range(1, 7)]}],
        "stop_rule": "Stop new dispatch after any failed/unknown transport, unexpected neutral output, or cost-bound violation; no retries or subsequent phase",
        "credentials": "Normal borrowed client environment key and inherited proxy/CA; no bypass, token display, credential mutation or custom authorization injection",
        "unknown_cost_policy": "Each started call without finite provider bill retains its .02 reserve",
        "hypothesis": "Lower simultaneous requests may avoid the prior launch's HTTP401; success does not establish a root cause"}
    save(HERE / "plan.json", plan)
    return save(HERE / "FREEZE.json", {"frozen_at": now(), "sha256": {
        "diagnose.py": sha(HERE / "diagnose.py"), "plan.json": sha(HERE / "plan.json"),
        "../controlplane_20261015/api_client.py": sha(CLIENT)}})


class Diagnostic:
    def __init__(self):
        self.plan = load(HERE / "plan.json")
        frozen = load(HERE / "FREEZE.json")
        for name, expected in frozen["sha256"].items():
            if sha(HERE / name) != expected:
                raise RuntimeError("Frozen diagnostic source changed")
        module_spec = importlib.util.spec_from_file_location("diagnostic_transport", CLIENT)
        self.client = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(self.client)
        self.client.MAX_ATTEMPTS = 1
        self.lock = threading.Lock()
        self.stop = threading.Event()

    def accounted(self):
        total = 0
        for path in (HERE / "calls").glob("*/budget_reservation.json"):
            bill = load(path.parent / "call.json").get("usage", {}).get("cost") if (path.parent / "call.json").exists() else None
            known = isinstance(bill, (int, float)) and not isinstance(bill, bool) and math.isfinite(bill) and bill >= 0
            total += float(bill) if known else self.plan["per_started_call_reserve_usd"]
        return total

    def one(self, call_id):
        path = HERE / "calls" / call_id
        with self.lock:
            if self.stop.is_set():
                return {"call_id": call_id, "dispatched": False, "pass": False}
            reservation = path / "budget_reservation.json"
            if not reservation.exists():
                if self.accounted() + .02 > .25 + 1e-12:
                    self.stop.set()
                    raise RuntimeError("Diagnostic cap would be exceeded")
                save(reservation, {"reserved_at": now(), "reserved_usd": .02,
                    "messages_sha256": hashlib.sha256(canonical(self.plan["messages"])).hexdigest()})
        try:
            record = self.client.call(self.plan["messages"], None, self.plan["model"], path,
                temperature=self.plan["temperature"], max_tokens=self.plan["max_tokens"])
            bill = record.get("usage", {}).get("cost")
            known = isinstance(bill, (int, float)) and not isinstance(bill, bool) and math.isfinite(bill) and bill >= 0
            try:
                neutral = self.client.strict_json(record.get("raw_content")) == {"ok": True}
            except (ValueError, TypeError, RecursionError):
                neutral = False
            passed = record.get("status") == "completed" and neutral and (not known or bill <= .02)
            result = {"call_id": call_id, "dispatched": True, "pass": passed,
                "status": record.get("status"), "http_status": record.get("http_status"),
                "neutral_output_valid": neutral, "provider_cost_usd": float(bill) if known else None,
                "accounted_cost_usd": float(bill) if known else .02,
                "provider_response_id": record.get("provider_response_id")}
        except Exception as exc:
            passed = False
            result = {"call_id": call_id, "dispatched": True, "pass": False,
                "status": "exception", "error_type": type(exc).__name__, "accounted_cost_usd": .02}
        if not passed:
            self.stop.set()
        save(path / "diagnostic_result.json", result)
        return result

    def run(self):
        results = []
        for phase in self.plan["phases"]:
            if self.stop.is_set():
                break
            if phase["workers"] == 1:
                for call_id in phase["call_ids"]:
                    results.append(self.one(call_id))
                    if self.stop.is_set():
                        break
            else:
                pending_ids = iter(phase["call_ids"])
                with ThreadPoolExecutor(max_workers=3) as pool:
                    pending = {pool.submit(self.one, next(pending_ids)) for _ in range(3)}
                    while pending:
                        done, pending = wait(pending, return_when=FIRST_COMPLETED)
                        batch = [future.result() for future in done]
                        results.extend(batch)
                        if self.stop.is_set() or any(not result["pass"] for result in batch):
                            self.stop.set()
                            continue
                        for _ in range(len(batch)):
                            call_id = next(pending_ids, None)
                            if call_id is not None:
                                pending.add(pool.submit(self.one, call_id))
            print(json.dumps({"phase": phase["name"], "completed": sum(r["dispatched"] for r in results),
                              "all_so_far_pass": all(r["pass"] for r in results)}), flush=True)
        return save(HERE / "RESULT.json", {"finished_at": now(),
            "pass": len(results) == 12 and all(r["pass"] for r in results),
            "requests_dispatched": sum(r["dispatched"] for r in results),
            "results": sorted(results, key=lambda r: r["call_id"]),
            "budget_accounted_usd": self.accounted(), "cap_usd": .25,
            "interpretation": "Transport-only diagnostic; no behavioral finding or causal attribution"})


if __name__ == "__main__":
    if sys.argv[1:] == ["prepare"]:
        result = prepare()
    elif sys.argv[1:] == ["run"]:
        result = Diagnostic().run()
    else:
        raise SystemExit("Use prepare or run")
    print(json.dumps(result, indent=2))
