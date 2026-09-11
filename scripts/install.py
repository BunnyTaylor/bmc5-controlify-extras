#!/usr/bin/env python3
"""Install BMC5 Controlify Extras into a Prism/MultiMC instance.

Usage:
    scripts/install.py <path-to-instance>/minecraft [--deck] [--dry-run]

<path> may be either the instance folder or its inner `minecraft/` (.minecraft)
folder; both are accepted.

What it does:
  1. Builds + copies the resource pack into  resourcepacks/
  2. Enables it in  options.txt  (appended last, so its Controlify
     defaults take priority over every other pack)
  3. Adds Xaero / FTB Quests screens to Controlify's virtual-mouse list in
     config/controlify.json  so those GUIs are usable with a stick cursor
  4. --deck only: moves four actions onto unused numpad keys so the Steam
     Deck's L4/L5/R4/R5 can drive them through Steam Input without
     colliding with any other mod's keybind

Every file it edits is backed up next to the original as *.bak-<timestamp>.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
import zipfile
from pathlib import Path

PACK_NAME = "BMC5-Controlify-Extras.zip"
PACK_ENTRY = f"file/{PACK_NAME}"

# Screens that are drawn by hand rather than out of vanilla widgets. Controlify
# can't tab-navigate these, so they need the virtual mouse cursor instead.
# Unknown class names are silently dropped by Controlify (ClassNotFoundException
# -> Stream.empty), so listing a mod that isn't installed is harmless.
VIRTUAL_MOUSE_SCREENS = [
    "xaero.lib.client.gui.ScreenBase",             # world map, waypoint list, add waypoint
    "xaero.lib.client.gui.config.EditConfigScreen",  # Xaero settings screens
    "dev.ftb.mods.ftblibrary.ui.BaseScreen",       # FTB Quests book
]

# Deck back buttons -> unused numpad keys. Verified free against all 218
# keybinds in BMC5 v52 (Jade uses numpad 0-5, Xaero uses numpad +).
DECK_KEYS = {
    "key_justzoom.keybinds.keybind.zoom": "key.keyboard.keypad.6",   # L4 hold = zoom
    "key_key.veinmining.activate.desc":   "key.keyboard.keypad.7",   # L5 hold = vein mine
    "key_key.backpacked.open_backpack":   "key.keyboard.keypad.8",   # R4 = backpack
    "key_gui.xaero_open_map":             "key.keyboard.keypad.9",   # R5 = world map
}

STAMP = time.strftime("%Y%m%d-%H%M%S")


def log(msg: str) -> None:
    print(f"  {msg}")


def backup(path: Path, dry: bool) -> None:
    dest = path.with_suffix(path.suffix + f".bak-{STAMP}")
    if not dry:
        shutil.copy2(path, dest)
    log(f"backed up {path.name} -> {dest.name}")


def resolve_instance(raw: Path) -> Path:
    """Accept either the instance dir or the inner minecraft/.minecraft dir."""
    if (raw / "options.txt").exists():
        return raw
    for inner in ("minecraft", ".minecraft"):
        if (raw / inner / "options.txt").exists():
            return raw / inner
    sys.exit(f"error: no options.txt found under {raw} — is that the instance folder?")


def build_pack(repo: Path, dry: bool) -> Path:
    """Zip pack/ into dist/. Stored at the archive root, as Minecraft expects."""
    src = repo / "pack"
    out = repo / "dist" / PACK_NAME
    if dry:
        log(f"would build {out}")
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(src.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(src).as_posix())
    log(f"built {out.name}")
    return out


def install_pack(zip_path: Path, mc: Path, dry: bool) -> None:
    dest_dir = mc / "resourcepacks"
    if not dry:
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(zip_path, dest_dir / PACK_NAME)
    log(f"installed pack -> resourcepacks/{PACK_NAME}")


def enable_pack(mc: Path, dry: bool) -> None:
    """Append our entry to the resourcePacks list, last = highest priority.

    Edited as a string rather than re-serialised, so the rest of the line keeps
    whatever escaping Minecraft wrote (e.g. \\u0027 for apostrophes).
    """
    opts = mc / "options.txt"
    lines = opts.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = False
    for i, line in enumerate(lines):
        if not line.startswith("resourcePacks:"):
            continue
        if PACK_ENTRY in line:
            log("pack already enabled in options.txt")
            return
        stripped = line.rstrip("\n")
        if not stripped.endswith("]"):
            log("! resourcePacks line looks unusual — enable the pack manually")
            return
        sep = "" if stripped.endswith("[]") else ","
        lines[i] = f'{stripped[:-1]}{sep}"{PACK_ENTRY}"]\n'
        changed = True
        break
    if not changed:
        log("! no resourcePacks line found — enable the pack manually")
        return
    if not dry:
        backup(opts, dry)
        opts.write_text("".join(lines), encoding="utf-8")
    log("enabled pack in options.txt (last = highest priority)")


def patch_controlify(mc: Path, dry: bool) -> None:
    cfg = mc / "config" / "controlify.json"
    if not cfg.exists():
        log("! config/controlify.json not found — launch the game once, then re-run")
        return
    data = json.loads(cfg.read_text(encoding="utf-8"))
    screens = data.setdefault("global", {}).setdefault("virtual_mouse_screens", [])
    added = [s for s in VIRTUAL_MOUSE_SCREENS if s not in screens]
    if not added:
        log("virtual-mouse screens already present")
        return
    screens.extend(added)
    if not dry:
        backup(cfg, dry)
        cfg.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    for s in added:
        log(f"virtual mouse enabled for {s}")


def patch_deck_keys(mc: Path, dry: bool) -> None:
    opts = mc / "options.txt"
    lines = opts.read_text(encoding="utf-8").splitlines(keepends=True)
    seen, changed = set(), False
    for i, line in enumerate(lines):
        key = line.split(":", 1)[0]
        if key in DECK_KEYS:
            seen.add(key)
            want = f"{key}:{DECK_KEYS[key]}\n"
            if line != want:
                lines[i] = want
                changed = True
                log(f"{key} -> {DECK_KEYS[key]}")
    for missing in sorted(set(DECK_KEYS) - seen):
        log(f"! {missing} not in options.txt — skipped")
    if not changed:
        log("deck keybinds already set")
        return
    if not dry:
        backup(opts, dry)
        opts.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Install BMC5 Controlify Extras.")
    ap.add_argument("instance", type=Path, help="instance folder (or its minecraft/ dir)")
    ap.add_argument("--deck", action="store_true",
                    help="also remap 4 actions to free numpad keys for Steam Deck back buttons")
    ap.add_argument("--dry-run", action="store_true", help="show changes without writing")
    args = ap.parse_args()

    repo = Path(__file__).resolve().parent.parent
    mc = resolve_instance(args.instance.expanduser().resolve())
    dry = args.dry_run

    print(f"Instance: {mc}{'  (dry run)' if dry else ''}\n")
    print("Resource pack:")
    install_pack(build_pack(repo, dry), mc, dry)
    enable_pack(mc, dry)
    print("\nControlify global config:")
    patch_controlify(mc, dry)
    if args.deck:
        print("\nSteam Deck keybinds:")
        patch_deck_keys(mc, dry)
    print("\nDone. Restart Minecraft (or press F3+T) to load the pack.")


if __name__ == "__main__":
    main()
