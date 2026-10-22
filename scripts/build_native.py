"""Build an offline native distribution on the target OS and CPU architecture."""
from __future__ import annotations

import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import ssl
import tarfile
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
VERSION = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))["version"]
SYSTEM = {"win32": "windows", "darwin": "macos", "linux": "linux"}.get(sys.platform)
if SYSTEM is None:
    raise SystemExit("Unsupported build platform")
ARCH = {"amd64": "x64", "x86_64": "x64", "aarch64": "arm64", "arm64": "arm64"}.get(platform.machine().lower())
if ARCH is None:
    raise SystemExit("Unsupported CPU architecture")
NAME = f"ClashStudio-v{VERSION}-{SYSTEM}-{ARCH}"
BUILD = ROOT / "build" / "native" / f"{SYSTEM}-{ARCH}"
OUT = ROOT / "releases"
BUILD.mkdir(parents=True, exist_ok=True)
OUT.mkdir(exist_ok=True)


def run(*args):
    subprocess.run([str(a) for a in args], cwd=ROOT, check=True)


def copy_notices(destination):
    licenses = destination / "LICENSES"
    licenses.mkdir()
    for dist in metadata.distributions():
        name = dist.metadata.get("Name", "unknown")
        safe = "".join(c for c in name if c.isalnum() or c in "-_+.")
        for entry in dist.files or []:
            if entry.name.lower().startswith(("license", "copying", "notice")):
                source = Path(dist.locate_file(entry))
                if source.is_file():
                    target = licenses / safe / entry.name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if target.exists() and target.read_bytes() != source.read_bytes():
                        target = target.with_name(str(len(list(target.parent.iterdir()))) + "-" + target.name)
                    shutil.copy2(source, target)
    for base in (Path(sys.base_prefix), Path(sys.base_prefix) / "lib"):
        for name in ("LICENSE", "LICENSE.txt", "LICENSE.rst"):
            if (base / name).is_file():
                shutil.copy2(base / name, licenses / "Python-LICENSE.txt")
                break
    distributions = sorted(f"{d.metadata.get('Name', 'unknown')}=={d.version}" for d in metadata.distributions())
    (destination / "DEPENDENCIES.txt").write_text(
        f"Python {platform.python_version()}\nPlatform: {SYSTEM}-{ARCH}\n\n" + "\n".join(distributions) + "\n", encoding="utf-8")


if not (ROOT / "frontend/dist/index.html").is_file():
    raise SystemExit("Build frontend first")
run(sys.executable, ROOT / "scripts/package.py")
args = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir", "--name", "ClashStudio",
        "--distpath", BUILD / "dist", "--workpath", BUILD / "work", "--specpath", BUILD,
        "--add-data", str(ROOT / "frontend/dist") + os.pathsep + "frontend/dist",
        "--add-data", str(ROOT / "examples") + os.pathsep + "examples",
        "--hidden-import", "uvicorn.logging", "--hidden-import", "uvicorn.loops.asyncio",
        "--hidden-import", "uvicorn.lifespan.on", "--hidden-import", "uvicorn.protocols.http.h11_impl",
        "--collect-all", "ruamel.yaml"]
# Some managed Python distributions load an additional public CA policy file
# relative to ssl.py. Preserve that policy when freezing rather than bypass it.
runtime_ca_policy = Path(ssl.__file__).parent / "codex-rejected-cas.pem"
if runtime_ca_policy.is_file():
    args += ["--add-data", str(runtime_ca_policy) + os.pathsep + "."]
if SYSTEM == "macos":
    args += ["--windowed", "--osx-bundle-identifier", "io.github.zheng0625.clashstudio"]
args.append(ROOT / "run.py")
run(*args)

with tempfile.TemporaryDirectory(prefix="stage-", dir=BUILD) as temporary:
    stage = Path(temporary) / NAME
    if SYSTEM == "macos":
        stage.mkdir()
        shutil.copytree(BUILD / "dist/ClashStudio.app", stage / "ClashStudio.app", symlinks=True)
        start = '#!/bin/bash\ncd -- "$(dirname -- "$0")"\nopen ./ClashStudio.app\n'
        stop = '#!/bin/bash\ncd -- "$(dirname -- "$0")"\n./ClashStudio.app/Contents/MacOS/ClashStudio --stop "$@"\n'
        for name, content in (("Start.command", start), ("Stop.command", stop)):
            (stage / name).write_text(content, encoding="utf-8")
            (stage / name).chmod(0o755)
    else:
        shutil.copytree(BUILD / "dist/ClashStudio", stage, symlinks=True)
        if SYSTEM == "windows":
            (stage / "Start.cmd").write_bytes(b'@echo off\r\n"%~dp0ClashStudio.exe" %*\r\n')
            (stage / "Stop.cmd").write_bytes(b'@echo off\r\n"%~dp0ClashStudio.exe" --stop %*\r\n')
            for name in ("configure-lan-firewall.ps1", "配置局域网防火墙.cmd"):
                shutil.copy2(ROOT / name, stage / name)
        else:
            for name, flag in (("Start.sh", ""), ("Stop.sh", "--stop ")):
                (stage / name).write_text('#!/bin/sh\ncd -- "$(dirname -- "$0")"\nexec ./ClashStudio ' + flag + '"$@"\n', encoding="utf-8")
                (stage / name).chmod(0o755)
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md", "README.md", "README.en.md", "CHANGELOG.md", "SECURITY.md", "CONTRIBUTING.md"):
        shutil.copy2(ROOT / name, stage / name)
    shutil.copytree(ROOT / "docs", stage / "docs", ignore=shutil.ignore_patterns("__pycache__"))
    (stage / "Source").mkdir()
    source = OUT / f"ClashStudio-v{VERSION}-source.zip"
    shutil.copy2(source, stage / "Source" / source.name)
    copy_notices(stage)
    manifest = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(stage).as_posix()}\n"
                       for p in sorted(stage.rglob("*")) if p.is_file() and not p.is_symlink())
    (stage / "MANIFEST.sha256").write_text(manifest, encoding="utf-8")
    if SYSTEM == "windows":
        archive = OUT / (NAME + ".zip")
        with ZipFile(archive, "w", ZIP_DEFLATED) as zipped:
            for file in stage.rglob("*"):
                if file.is_file():
                    zipped.write(file, Path(NAME) / file.relative_to(stage))
    else:
        archive = OUT / (NAME + ".tar.gz")
        with tarfile.open(archive, "w:gz", dereference=False) as tar:
            tar.add(stage, arcname=NAME)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_name(archive.name + ".sha256").write_text(f"{digest}  {archive.name}\n", encoding="ascii")
    print(f"Native package ready: {archive.name} ({archive.stat().st_size:,} bytes)")
