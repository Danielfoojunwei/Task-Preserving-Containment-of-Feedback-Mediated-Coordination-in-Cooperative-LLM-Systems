"""Deterministic, shuffled run manifests with disjoint task splits."""
from __future__ import annotations
import argparse
import itertools
import json
import random
from pathlib import Path
from .core import Cell, canonical
from hashlib import sha256

SPLITS = {"development": list(range(1, 6)), "pilot": list(range(101, 106)),
          "heldout": list(range(1001, 1011))}

def make_manifest(split="pilot", n_seeds=5, peer_ablation=False, adaptive=False,
                  randomization_seed=20261014):
    if split not in SPLITS or not 1 <= n_seeds <= len(SPLITS[split]):
        raise ValueError("invalid split or seed count")
    feedbacks = ["original", "suppress_score"] + (["peer_snapshot"] if peer_ablation else [])
    cells = [Cell(s, z, c, f, split=split).to_dict()
             for s, z, c, f in itertools.product(SPLITS[split][:n_seeds],
                  ["cooperative", "coalition"], [False, True], feedbacks)]
    if adaptive:
        for s, z, c, mode in itertools.product(SPLITS[split][:n_seeds],
                  ["cooperative", "coalition"], [False, True], ["history_rule", "memoryless_rule"]):
            cells.append(Cell(s,z,c,"original",controller=mode,split=split).to_dict())
    random.Random(randomization_seed).shuffle(cells)
    body = {"schema":1, "split":split, "randomization_seed":randomization_seed,
            "evidence_type":"PLANNED_NOT_EXECUTED", "initial_private_channel":True,
            "revocation_boundary":"before_first_execution_turn_after_two_planning_rounds",
            "feedback_boundary":"before_first_execution_turn",
            "num_agents":4, "num_colluders":2, "planning_rounds":2,
            "max_conversation_steps":3, "cells":cells}
    body["manifest_sha256"] = sha256(canonical(body)).hexdigest()
    return body

def validate_manifest(m):
    body = dict(m); digest = body.pop("manifest_sha256")
    if sha256(canonical(body)).hexdigest() != digest:
        raise ValueError("manifest changed after freeze")
    keys = [Cell(**x).key for x in m["cells"]]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate cells")
    return [Cell(**x) for x in m["cells"]]

def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True)
    p.add_argument("--split",choices=SPLITS,default="pilot")
    p.add_argument("--seeds",type=int,default=5);p.add_argument("--peer-ablation",action="store_true")
    p.add_argument("--adaptive",action="store_true");a=p.parse_args()
    m=make_manifest(a.split,a.seeds,a.peer_ablation,a.adaptive)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(m,indent=2)+"\n")
    print(json.dumps({"planned_episodes":len(m["cells"]),"sha256":m["manifest_sha256"]}))
if __name__=="__main__":main()
