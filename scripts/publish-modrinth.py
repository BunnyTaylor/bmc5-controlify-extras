#!/usr/bin/env python3
"""Upload a built pack to an existing Modrinth project.

Create the project once in the web UI (https://modrinth.com/dashboard) — it
asks for the licence, summary, icon and gallery, which is quicker to fill in
there than over the API. After that, this script handles the repetitive part:
publishing each new version.

    export MODRINTH_TOKEN=mrp_...          # Settings -> PATs, scope: Create versions
    scripts/publish-modrinth.py --project bmc5-controlify-extras

Defaults come from VERSION and dist/. Use --dry-run to see the payload without
sending it.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests

API = "https://api.modrinth.com/v2"
UA = "BunnyTaylor/bmc5-controlify-extras (github.com/BunnyTaylor)"

# Controlify reads these packs through the resource-pack stack, so on Modrinth
# this is a resourcepack project whose only loader is "minecraft".
LOADERS = ["minecraft"]
GAME_VERSIONS = ["1.21.1"]


def main() -> None:
    repo = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description="Publish a version to Modrinth.")
    ap.add_argument("--project", required=True, help="project id or slug")
    ap.add_argument("--version", default=None, help="version number (default: VERSION file)")
    ap.add_argument("--file", action="append", default=None,
                    help="file to upload; repeatable (default: dist/*.zip)")
    ap.add_argument("--changelog", default=None, help="changelog text (default: CHANGELOG entry)")
    ap.add_argument("--game-versions", nargs="+", default=GAME_VERSIONS)
    ap.add_argument("--type", default="release", choices=["release", "beta", "alpha"])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    token = os.environ.get("MODRINTH_TOKEN")
    if not token and not args.dry_run:
        sys.exit("error: set MODRINTH_TOKEN (Modrinth -> Settings -> PATs, scope 'Create versions')")

    version = args.version or (repo / "VERSION").read_text().strip()
    if args.file:
        files = [Path(f) for f in args.file]
    else:
        # The main pack must be first: Modrinth treats files[0] as the primary
        # download, and the dragons add-on is optional. Plain sorted() would put
        # "Dragons" ahead of "Extras".
        found = sorted((repo / "dist").glob("*.zip"))
        files = ([f for f in found if "Dragons" not in f.name]
                 + [f for f in found if "Dragons" in f.name])
    if not files:
        sys.exit("error: nothing to upload — run scripts/install.py or build the packs first")
    for f in files:
        if not f.is_file():
            sys.exit(f"error: {f} not found")

    changelog = args.changelog or f"See the release notes for {version}."
    data = {
        "name": f"v{version}",
        "version_number": version,
        "changelog": changelog,
        "dependencies": [],
        "game_versions": args.game_versions,
        "version_type": args.type,
        "loaders": LOADERS,
        "featured": True,
        "project_id": args.project,
        "file_parts": [f.name for f in files],
        "primary_file": files[0].name,
    }

    print(f"Project : {args.project}")
    print(f"Version : {version} ({args.type})")
    print(f"MC      : {', '.join(args.game_versions)}")
    print("Files   :")
    for f in files:
        print(f"  {f.name}  ({f.stat().st_size} bytes)"
              + ("  [primary]" if f.name == data['primary_file'] else ""))

    if args.dry_run:
        print("\n--dry-run, not sending. Payload:")
        print(json.dumps(data, indent=2))
        return

    multipart = [("data", (None, json.dumps(data), "application/json"))]
    multipart += [(f.name, (f.name, f.read_bytes(), "application/zip")) for f in files]

    r = requests.post(f"{API}/version", headers={"Authorization": token, "User-Agent": UA},
                      files=multipart, timeout=120)
    if not r.ok:
        sys.exit(f"\nupload failed: HTTP {r.status_code}\n{r.text}")
    print(f"\nPublished: https://modrinth.com/resourcepack/{args.project}/version/{version}")


if __name__ == "__main__":
    main()
