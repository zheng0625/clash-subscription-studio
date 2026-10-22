#!/bin/bash
studio_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
exec /bin/bash "$studio_dir/start.sh" "$@"
