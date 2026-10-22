# Contributing

Contributions are welcome under GPL-3.0-only. Keep changes focused and describe the behavior and compatibility impact. Never include real subscription links, tokens, node credentials, user databases or screenshots containing them.

## Local development

Python 3.11+ and Node.js 20.19+ or 22.12+ are required. In `frontend/`, install with `pnpm install --frozen-lockfile`, then run `pnpm build`. In the project root, create a Python virtual environment and install `requirements-dev.txt`.

Run `python run.py --no-browser` from that environment. The administration service binds to loopback. Use an isolated `CLASH_STUDIO_DATA` directory and a separate port for development involving imports or writes.

When checking changes, build the frontend first, then run `python -m pytest -q`. Do not build concurrently with backend checks because they read the built assets. Existing browser checks in `scripts/ui-check.cjs` use Playwright and an isolated service at port 8766; install Playwright separately if using them.

Run `python scripts/package.py` after building to generate the candidate ZIP and its SHA-256 checksum. Runtime data and dependency directories are excluded.
