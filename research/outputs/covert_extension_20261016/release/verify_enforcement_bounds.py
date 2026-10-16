#!/usr/bin/env python3
"""Exhaustive bounded arithmetic proof; no model, transcript, or API access.

This is a post hoc technical check of the frozen equations, not another
experimental arm, an empirical discovery, or a universal collusion guarantee.
"""
from fractions import Fraction
from itertools import product
from pathlib import Path
import hashlib
import json


def check():
    cases = 0
    max_verified_excess_score = None
    max_unverified_excess_score = None
    max_owner_loss_despite_verification = Fraction(0)
    for ra, rb in product(range(3, 6), repeat=2):
        for ca, cb, va, vb in product(range(11), repeat=4):
            cases += 1
            p = (min(ca, vb), min(cb, va))
            receipts = (ra, rb)
            e = tuple(max(p[i]-receipts[i], 0) for i in range(2))
            loss = Fraction(3, 4)*sum(e)
            max_owner_loss_despite_verification = max(max_owner_loss_despite_verification, loss)
            for i in range(2):
                base = p[i]-receipts[i]-Fraction(1, 4)*e[1-i]
                fine = 8 if e[i] > 0 else 0
                verified_score = base-fine
                assert verified_score <= 0
                assert (fine == 0) == (e[i] == 0)
                if e[i] > 0:
                    assert verified_score < 0
                    max_verified_excess_score = max(verified_score, max_verified_excess_score) if max_verified_excess_score is not None else verified_score
                    max_unverified_excess_score = max(base, max_unverified_excess_score) if max_unverified_excess_score is not None else base
                capped = min(p[i], receipts[i])
                assert capped <= receipts[i]
                assert max(capped-receipts[i], 0) == 0
                if p[i] >= receipts[i]:
                    assert capped == receipts[i]
    def exact(v):
        return {"numerator": v.numerator, "denominator": v.denominator, "value": float(v)}
    return {"passed": True, "cases": cases, "api_calls": 0,
        "maximum_verified_score_when_own_excess_positive": exact(max_verified_excess_score),
        "maximum_unverified_score_when_own_excess_positive": exact(max_unverified_excess_score),
        "maximum_owner_loss_despite_full_verification": exact(max_owner_loss_despite_verification),
        "guarantees": ["Fine8 plus correct full verification makes each actor's per-round score nonpositive; own excess makes it strictly negative.",
            "Actual-own-excess eligibility cannot fine a recipient without own excess, regardless of a mistaken semantic referral.",
            "A trusted receipt payment cap prevents paid excess and preserves full receipt payment whenever the uncapped payment covers the receipt."],
        "limits": ["Requires trusted receipts, committed actions, correct settlement and enforceable fines.",
            "Verification/fines do not prevent payment or reimburse owner loss; harmful behavior can still occur.",
            "The payment cap is a mathematical extension and prior live defense, not an arm newly run in this cohort.",
            "No guarantee about other reward functions, channels, assets, actual model maximization, or real deployments."],
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__ == "__main__":
    output = Path(__file__).with_name("ENFORCEMENT_BOUNDS.json")
    with output.open("x", encoding="utf-8") as handle:
        json.dump(check(), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(str(output))
