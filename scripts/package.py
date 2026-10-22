"""Build a clean source + built-interface candidate from an allowlist."""
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
VERSION = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))["version"]
NAME = f"ClashStudio-v{VERSION}"
OUT = ROOT / "releases"
OUT.mkdir(exist_ok=True)
files = [ROOT / name for name in (
    ".gitignore", ".gitattributes", "LICENSE", "THIRD_PARTY_NOTICES.md", "README.md",
    "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md", "requirements.txt", "requirements-dev.txt",
    "run.py", "start.ps1", "stop.ps1", "启动软件.cmd", "停止服务.cmd",
    "configure-lan-firewall.ps1", "配置局域网防火墙.cmd", "frontend/package.json",
    "frontend/pnpm-lock.yaml", "frontend/pnpm-workspace.yaml", "frontend/tsconfig.json",
    "frontend/vite.config.ts", "frontend/index.html",
)]
allowed = {".py", ".md", ".yaml", ".yml", ".vue", ".ts", ".css", ".html", ".js", ".cjs", ".svg", ".png", ".webp"}
for folder in ("app", "docs", "examples", "frontend/src", "frontend/dist", "tests", "scripts", ".github"):
    files.extend(p for p in (ROOT / folder).rglob("*")
                 if p.is_file() and p.suffix in allowed and "__pycache__" not in p.parts)
files = sorted(set(files))
if not (ROOT / "frontend/dist/index.html").is_file():
    raise SystemExit("Build frontend before packaging.")
for p in files:
    if p.is_symlink() or not p.resolve().is_relative_to(ROOT.resolve()):
        raise SystemExit("Refusing a symlink or a file outside the workspace.")
manifest = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}\n" for p in files)
output = OUT / f"{NAME}.zip"
with ZipFile(output, "w", ZIP_DEFLATED) as archive:
    for file in files:
        archive.write(file, Path(NAME) / file.relative_to(ROOT))
    archive.writestr(f"{NAME}/MANIFEST.sha256", manifest)
digest = hashlib.sha256(output.read_bytes()).hexdigest()
(OUT / f"{NAME}.sha256").write_text(f"{digest}  {output.name}\n", encoding="ascii")
print(f"Packaged {len(files)} allowlisted files: {output.name} ({output.stat().st_size:,} bytes)")
print(f"SHA256: {digest}")
