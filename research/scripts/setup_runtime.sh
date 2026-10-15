#!/usr/bin/env bash
# Run from the real Colosseum checkout after fork_and_publish.sh.
set -euo pipefail
ROOT="${1:-$PWD}"
[[ -f "$ROOT/uv.lock" && -f "$ROOT/experiments/collusion/run.py" ]] || { echo 'Not a Colosseum checkout' >&2; exit 2; }
command -v uv >/dev/null || { echo 'Install uv first' >&2; exit 2; }
cd "$ROOT"
# Follow the repository lock rather than silently upgrading Terrarium.
uv venv --python 3.11 .venv
uv sync --frozen --no-install-project
# CoLLAB is required by some environment imports. Use the existing submodule metadata.
if [[ -f .gitmodules ]]; then git submodule update --init --recursive; fi
.venv/bin/python -m pip --version >/dev/null 2>&1 || true
