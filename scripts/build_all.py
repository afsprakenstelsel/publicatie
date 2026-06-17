#!/usr/bin/env python3
"""
Bouw alle versies uit releases.json naar site/ subdirectories.

Elke versie wordt als git-worktree uitgecheckt, voorzien van de meest recente
buildtools (generate_docs.py, custom_theme, releases.json) en gebouwd naar
site/{path}/. Na afloop kan de volledige site geserveerd worden met:

    python -m http.server 8080 --directory site/

En bereikbaar zijn via http://localhost:8080/
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list, cwd: Path, label: str) -> None:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"\n  ✗ {label} mislukt:")
        print(result.stdout[-1000:] if result.stdout else "")
        print(result.stderr[-1000:] if result.stderr else "")
        raise SystemExit(1)


def build_version(version: dict) -> None:
    vid        = version["id"]
    git_ref    = version["git_ref"]
    vpath      = version.get("path", "/").strip("/")   # '' voor root, 'v1.1' etc.
    parent_ref = version.get("parent_ref")

    site_dir = ROOT / "site" / vpath if vpath else ROOT / "site"
    label    = f"{vid} ({git_ref})"

    print(f"\n▸  {label}")
    print(f"   → {site_dir.relative_to(ROOT)}")

    wt = Path(tempfile.mkdtemp(prefix="medmij-wt-"))
    try:
        # Git worktree aanmaken (detached, zodat branches en tags beiden werken)
        run(
            ["git", "worktree", "add", "--detach", str(wt), git_ref],
            cwd=ROOT, label="git worktree add",
        )

        # Overschrijf buildtools in de worktree met de versie uit main
        # (zodat de versie-picker altijd aanwezig is, ook in oudere versies)
        shutil.copy2(ROOT / "scripts/generate_docs.py", wt / "scripts/generate_docs.py")
        shutil.copy2(ROOT / "releases.json",            wt / "releases.json")
        shutil.copytree(ROOT / "custom_theme", wt / "custom_theme", dirs_exist_ok=True)

        # Genereer docs (berekent diff als parent_ref bekend is)
        gen = [sys.executable, "scripts/generate_docs.py", "--version", vid]
        if parent_ref:
            gen += ["--compare-ref", parent_ref]
        run(gen, cwd=wt, label="generate_docs")

        # Kopieer mkdocs.yml naar de worktree (het origineel verwijst naar custom_theme)
        shutil.copy2(ROOT / "mkdocs.yml", wt / "mkdocs.yml")

        site_dir.mkdir(parents=True, exist_ok=True)
        run(
            [
                sys.executable, "-m", "mkdocs", "build",
                "--site-dir", str(site_dir.resolve()),
                "--quiet",
            ],
            cwd=wt, label="mkdocs build",
        )

        n_changes = len(version.get("parent_ref") and [] or [])
        print(f"   ✓ gereed")

    finally:
        subprocess.run(
            ["git", "worktree", "remove", str(wt), "--force"],
            cwd=ROOT, capture_output=True,
        )
        shutil.rmtree(wt, ignore_errors=True)


def serve(site_root: Path, port: int = 8080) -> None:
    import http.server
    import os
    import threading
    import webbrowser

    os.chdir(site_root)

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass  # stil

    httpd = http.server.HTTPServer(("", port), QuietHandler)
    url = f"http://localhost:{port}/"
    print(f"\n▸  Lokale preview op {url}")
    print(f"   Ctrl+C om te stoppen\n")
    threading.Timer(0.3, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer gestopt.")


def main() -> None:
    serve_after = "--serve" in sys.argv

    releases = json.loads((ROOT / "releases.json").read_text(encoding="utf-8"))
    versions = releases.get("versions", [])

    if not versions:
        print("Geen versies gevonden in releases.json.")
        raise SystemExit(1)

    print(f"Bouw {len(versions)} versie(s)...\n")

    site_root = ROOT / "site"
    if site_root.exists():
        shutil.rmtree(site_root)

    for version in versions:
        build_version(version)

    print(f"\n✓  Alle versies gebouwd in site/")

    if serve_after:
        serve(site_root)
    else:
        print(f"\nVoor lokale preview:  python scripts/build_all.py --serve")
        print(f"Voor deployment:      ghp-import site/ -p")


if __name__ == "__main__":
    main()
