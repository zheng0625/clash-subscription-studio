#!/usr/bin/env bash
set -euo pipefail
studio_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -x "$studio_dir/ClashStudio" ]]; then exec "$studio_dir/ClashStudio" --stop "$@"; fi
exec "$studio_dir/.venv/bin/python" "$studio_dir/run.py" --stop "$@"
