#!/usr/bin/env python3
"""Track and restore the mods you add on top of a CurseForge modpack.

Updating a managed pack in Prism replaces the instance's mod set with the new
version's, which drops anything you added yourself. This records those mods so
you can put them back in one command.

    scripts/local-mods.py list     "<instance>"   # what's yours vs the pack's
    scripts/local-mods.py snapshot "<instance>"   # record them into local-addons/
    scripts/local-mods.py restore  "<instance>"   # put back whatever is missing

How the two are told apart: Prism writes a metadata file per mod under
mods/.index/. Mods that came from the CurseForge pack carry an
[update.curseforge] block, while ones you installed yourself carry
[update.modrinth] (or no update block at all). A CurseForge pack's manifest is
entirely CurseForge, so anything non-curseforge is yours.

snapshot stores only those metadata files — a few KB each, and they carry the
download URL and SHA-512 — so restore can re-fetch the jars instead of the repo
carrying ~150 MB of them. A jar already sitting in local-addons/jars/ is used
instead of downloading.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import tomllib
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STORE = REPO / "local-addons"
JARS = STORE / "jars"
UA = "BunnyTaylor/bmc5-controlify-extras"


def resolve_instance(raw: Path) -> Path:
    if (raw / "mods").is_dir():
        return raw
    for inner in ("minecraft", ".minecraft"):
        if (raw / inner / "mods").is_dir():
            return raw / inner
    sys.exit(f"error: no mods/ directory under {raw}")


def classify(mc: Path) -> tuple[list[tuple[Path, dict]], int]:
    """Return ([(toml_path, parsed)], pack_count) — the local ones and a tally."""
    index = mc / "mods" / ".index"
    if not index.is_dir():
        sys.exit(f"error: {index} not found. Open the instance's Mods tab in "
                 "Prism once so it writes mod metadata, then retry.")
    local, pack = [], 0
    for f in sorted(index.glob("*.toml")):
        data = tomllib.loads(f.read_text(encoding="utf-8", errors="replace"))
        if "curseforge" in data.get("update", {}):
            pack += 1
        else:
            local.append((f, data))
    return local, pack


def verify(path: Path, want: str, fmt: str) -> bool:
    if not want or fmt not in ("sha512", "sha1", "sha256"):
        return True
    h = hashlib.new(fmt)
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest() == want


def cmd_list(mc: Path) -> None:
    local, pack = classify(mc)
    print(f"pack mods (curseforge): {pack}")
    print(f"your mods             : {len(local)}\n")
    for _, d in local:
        src = "modrinth" if "modrinth" in d.get("update", {}) else "hand-added"
        print(f"  {d.get('name', '?'):<38} {d.get('filename', '?')}  [{src}]")


def cmd_snapshot(mc: Path, stash_jars: bool) -> None:
    local, _ = classify(mc)
    if not local:
        print("no local-only mods found — nothing to record")
        return
    STORE.mkdir(exist_ok=True)
    for f, d in local:
        shutil.copy2(f, STORE / f.name)
        print(f"  recorded {d.get('name', f.stem)}")
        if stash_jars:
            jar = mc / "mods" / d["filename"]
            if jar.is_file():
                JARS.mkdir(parents=True, exist_ok=True)
                shutil.copy2(jar, JARS / jar.name)
                print(f"    stashed {jar.name} ({jar.stat().st_size // 1024 // 1024} MB)")
    print(f"\n{len(local)} mod(s) recorded in {STORE.relative_to(REPO)}/")
    print("Commit that directory — restore re-downloads the jars from it.")


def cmd_restore(mc: Path) -> None:
    tomls = sorted(STORE.glob("*.toml"))
    if not tomls:
        sys.exit(f"error: nothing recorded in {STORE} — run 'snapshot' first "
                 "(ideally while the instance still has your mods)")
    index = mc / "mods" / ".index"
    index.mkdir(parents=True, exist_ok=True)
    restored = skipped = failed = 0

    for t in tomls:
        d = tomllib.loads(t.read_text(encoding="utf-8", errors="replace"))
        name, filename = d.get("name", t.stem), d.get("filename")
        if not filename:
            print(f"  ! {t.name} has no filename field, skipping")
            failed += 1
            continue
        dest = mc / "mods" / filename
        if dest.is_file():
            print(f"  = {name} already present")
            skipped += 1
        else:
            dl = d.get("download", {})
            url, want, fmt = dl.get("url", ""), dl.get("hash", ""), dl.get("hash-format", "")
            stashed = JARS / filename
            if stashed.is_file():
                shutil.copy2(stashed, dest)
                print(f"  + {name} (from local stash)")
            elif url:
                print(f"  ↓ {name} …", flush=True)
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": UA})
                    with urllib.request.urlopen(req, timeout=180) as r, dest.open("wb") as out:
                        shutil.copyfileobj(r, out)
                except Exception as e:
                    print(f"    failed: {e}")
                    dest.unlink(missing_ok=True)
                    failed += 1
                    continue
                if not verify(dest, want, fmt):
                    print(f"    {fmt} mismatch — discarding")
                    dest.unlink(missing_ok=True)
                    failed += 1
                    continue
                print(f"    ok ({dest.stat().st_size // 1024} KB, {fmt} verified)")
            else:
                print(f"  ! {name}: not stashed and no download url")
                failed += 1
                continue
            restored += 1
        # keep Prism's mod list aware of it either way
        shutil.copy2(t, index / t.name)

    print(f"\nrestored {restored}, already present {skipped}, failed {failed}")
    if restored:
        print("Re-run scripts/install.py too — a pack update replaces options.txt,")
        print("which un-enables the resource packs and resets keybinds.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("action", choices=["list", "snapshot", "restore"])
    ap.add_argument("instance", type=Path)
    ap.add_argument("--stash-jars", action="store_true",
                    help="snapshot: also copy the jars into local-addons/jars/ "
                         "(gitignored; lets restore work offline)")
    args = ap.parse_args()
    mc = resolve_instance(args.instance.expanduser().resolve())
    print(f"Instance: {mc}\n")
    {"list": lambda: cmd_list(mc),
     "snapshot": lambda: cmd_snapshot(mc, args.stash_jars),
     "restore": lambda: cmd_restore(mc)}[args.action]()


if __name__ == "__main__":
    main()
