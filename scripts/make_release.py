#!/usr/bin/env python3
"""
Build the Figshare bundles from a clean working copy.

    python scripts/make_release.py [--out dist] [--version v2.0]

Writes four archives and CHECKSUMS.txt. Caches, virtual environments and the
git directory are excluded, so the code bundle is exactly what a reader needs
and nothing else.
"""

from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path

EXCLUDE_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache",
                "dist", "runs", "telemetry", "_p3_pkg", ".idea", ".vscode"}
EXCLUDE_SUFFIX = {".pyc", ".pyo", ".DS_Store"}

BUNDLES = {
    "Industry50-MultiRobot-Scalability-code": ["."],
    "data_processed": ["data/processed"],
    "data_ensemble": ["data/ensemble"],
    "figures": ["figures"],
}


def keep(p: Path, root: Path) -> bool:
    rel = p.relative_to(root)
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return False
    if p.suffix in EXCLUDE_SUFFIX:
        return False
    return p.is_file()


def build(root: Path, name: str, sources, out: Path, version: str) -> Path | None:
    files = []
    for src in sources:
        base = (root / src).resolve()
        if not base.exists():
            continue
        for p in sorted(base.rglob("*")):
            if keep(p, root):
                files.append(p)
    if not files:
        print(f"  skip {name}: nothing to archive")
        return None
    target = out / f"{name}.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in files:
            z.write(p, Path(name) / p.relative_to(root))
        z.comment = f"{name} {version}".encode()
    size = target.stat().st_size
    print(f"  {target.name:48s} {len(files):5d} files  {size/1e6:8.2f} MB")
    return target


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist")
    ap.add_argument("--version", default="v2.0")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    out = root / args.out
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*"):
        old.unlink()

    print(f"building {args.version} from {root}\n")
    made = [b for b in (build(root, n, s, out, args.version)
                        for n, s in BUNDLES.items()) if b]

    lines = [f"# SHA-256 checksums, {args.version}", ""]
    for p in made:
        lines.append(f"{sha256(p)}  {p.name}")
    (out / "CHECKSUMS.txt").write_text("\n".join(lines) + "\n")

    print(f"\nwrote {out/'CHECKSUMS.txt'}")
    print("verify a download with:  sha256sum -c CHECKSUMS.txt")


if __name__ == "__main__":
    main()
