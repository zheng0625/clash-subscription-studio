#!/usr/bin/env bash
set -euo pipefail
studio_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$studio_dir"
if [[ -x "$studio_dir/ClashStudio" ]]; then exec "$studio_dir/ClashStudio" "$@"; fi
if ! command -v python3 >/dev/null; then echo 'Source checkout requires Python 3.11+. Download the native package to run without installing dependencies.' >&2; exit 1; fi
if [[ ! -x .venv/bin/python ]]; then python3 -m venv .venv; fi
requirements_hash="$(.venv/bin/python -c "import hashlib; print(hashlib.sha256(open('requirements.txt','rb').read()).hexdigest())")"
if [[ ! -f .venv/studio-requirements.sha256 ]] || [[ "$(cat .venv/studio-requirements.sha256)" != "$requirements_hash" ]]; then
  .venv/bin/python -m pip install -r requirements.txt
  printf '%s\n' "$requirements_hash" > .venv/studio-requirements.sha256
fi
if [[ ! -f frontend/dist/index.html ]]; then
  if ! command -v npm >/dev/null; then echo 'Source checkout requires Node.js/npm to build the interface. Native packages include it prebuilt.' >&2; exit 1; fi
  (cd frontend && npm install && npm run build)
fi
exec .venv/bin/python run.py "$@"
