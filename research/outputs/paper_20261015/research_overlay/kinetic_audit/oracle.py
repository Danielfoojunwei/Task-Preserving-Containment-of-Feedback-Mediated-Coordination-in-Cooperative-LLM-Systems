"""Small-instance exact enumeration using the REAL environment reward function.

Task economics are not reimplemented; duplicates/skip/penalties stay upstream.
"""
from itertools import product
from .core import finite_number

def exact_oracle(env, *, max_assignments=200000):
    names=list(env.get_agent_names())
    tasks=list(env.tasks)
    domains=tasks+["skip"]
    size=len(domains)**len(names)
    if size>max_assignments:
        raise ValueError(f"Enumeration exceeds limit ({size}>{max_assignments})")
    best=float("-inf");best_assignment=None
    for values in product(domains,repeat=len(names)):
        assignment=dict(zip(names,values))
        result=env._rewards(assignment)
        if isinstance(result,tuple) and len(result)>=2 and isinstance(result[1],dict):
            reward=finite_number(result[0])
        elif isinstance(result,dict):
            reward=sum(finite_number(v) for v in result.values())
        else:
            raise TypeError("Unrecognized reward API; no guessed economics permitted")
        if reward>best:
            best=reward;best_assignment=assignment
    return {"optimal_reward":best,"optimal_assignment":best_assignment,
            "assignments_enumerated":size,"oracle_kind":"exact_upstream_reward_enumeration"}
