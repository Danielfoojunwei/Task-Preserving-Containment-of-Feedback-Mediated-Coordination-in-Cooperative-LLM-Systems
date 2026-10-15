#!/usr/bin/env bash
# User-authorized fork + research-branch publication. Never writes upstream/main.
set -euo pipefail
EXPECTED_OWNER="${EXPECTED_GITHUB_OWNER:-danielfoojunwei774}"
UPSTREAM="umass-ai-safety/colosseum"
PIN="b077fe7e2f10566e92156cc12e06ffb2aac54790"
BRANCH="research/task-preserving-collusion"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${2:-$PWD/colosseum-research}"
if [[ "${1:-}" != "--publish" ]]; then
  printf 'Dry run only. Will fork %s into authenticated owner %s; clone to %s; publish only %s.\n' "$UPSTREAM" "$EXPECTED_OWNER" "$DEST" "$BRANCH"
  printf 'Execute: bash scripts/fork_and_publish.sh --publish /absolute/new/checkout\n'
  exit 0
fi
for cmd in gh git python3; do command -v "$cmd" >/dev/null || { echo "Missing $cmd" >&2; exit 2; }; done
[[ ! -e "$DEST" ]] || { echo "Refusing existing destination: $DEST" >&2; exit 2; }
gh auth status >/dev/null
OWNER="$(gh api user --jq .login)"
[[ "$OWNER" == "$EXPECTED_OWNER" ]] || { echo "Authenticated owner differs: $OWNER" >&2; exit 2; }
[[ "$OWNER" != "umass-ai-safety" ]] || { echo 'Refusing upstream owner' >&2; exit 2; }
# This creates/reuses the authenticated user's real GitHub fork, not a mirrored repo.
gh repo fork "$UPSTREAM" --clone=false --remote=false
META="$(gh api "repos/$OWNER/colosseum")"
python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["fork"] and d["parent"]["full_name"]=="umass-ai-safety/colosseum"' <<< "$META"
gh auth setup-git
git clone "https://github.com/$OWNER/colosseum.git" "$DEST"
git -C "$DEST" remote add upstream "https://github.com/$UPSTREAM.git"
git -C "$DEST" remote set-url --push upstream DISABLED
# Fetch only from the actual upstream pin; research branch is based on this commit.
git -C "$DEST" fetch upstream "$PIN"
git -C "$DEST" switch -c "$BRANCH" "$PIN"
OVERLAY="$DEST/research/kinetic_audit"
[[ ! -e "$OVERLAY" ]] || { echo "Refusing to overwrite existing research tree" >&2; exit 2; }
mkdir -p "$OVERLAY"
python3 - "$HERE" "$OVERLAY" <<'PY'
import pathlib,shutil,sys
src,dst=map(pathlib.Path,sys.argv[1:])
ignore=shutil.ignore_patterns('.git','.venv','__pycache__','.pytest_cache','outputs','raw_traces','.env','.env.*')
for p in src.iterdir():
    if p.name in {'.git','.venv','__pycache__','.pytest_cache','outputs','raw_traces'} or p.name.startswith('.env'):continue
    if p.is_dir():shutil.copytree(p,dst/p.name,ignore=ignore)
    else:shutil.copy2(p,dst/p.name)
PY
# Explicit paths only; do not stage unrelated files or credentials.
git -C "$DEST" add -- research/kinetic_audit
git -C "$DEST" -c user.name='Kinetic-Audit research build' -c user.email='research-build@users.noreply.github.com' commit -m 'research: add task-preserving collusion experiment overlay (no live results yet)'
ORIGIN="$(git -C "$DEST" remote get-url --push origin)"
[[ "$ORIGIN" == "https://github.com/$OWNER/colosseum.git" ]] || { echo 'Unexpected push destination' >&2; exit 2; }
git -C "$DEST" push -u origin "HEAD:refs/heads/$BRANCH"
echo "Published research branch: https://github.com/$OWNER/colosseum/tree/$BRANCH"
echo 'No PR to upstream was opened; no model calls were made.'
