#!/usr/bin/env python3
"""Remove a single mixin from a mod jar, leaving its version untouched.

For when a mod's compat mixin targets an API that has since changed, and the
mod's own fix only exists in a version you can't use — because a server pins the
old one, or a newer release drags in incompatible requirements.

Deleting one entry from the mixin config disables just that patch. The jar's
declared `version` is untouched, so a server still sees the same mod version and
the handshake is unaffected. Prefer a *client*-section mixin: those cannot touch
registries or server behaviour at all.

    scripts/disable-mixin.py <jar> <mixin-config.json> <mixin.ClassName>
    scripts/disable-mixin.py <jar> --list

Concretely, for BMC5: Supplementaries 3.5.34's compat.CompatEMFMixin injects
against an EMF constructor that gained a parameter back in EMF 3.2, so it fails
to apply the moment EMF builds a custom model — which is exactly when Fresh
Animations is enabled. The failed apply throws mid-resource-reload, the reload
aborts, and Minecraft reverts your pack selection.

    scripts/disable-mixin.py "<instance>/minecraft/mods/supplementaries-1.21-3.5.34-neoforge.jar" \\
        supplementaries-common.mixins.json compat.CompatEMFMixin

A pack update restores the stock jar, so re-run it afterwards.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("jar", type=Path)
    ap.add_argument("config", nargs="?", help="mixin config inside the jar")
    ap.add_argument("mixin", nargs="?", help="mixin class to remove")
    ap.add_argument("--list", action="store_true", help="list mixin configs in the jar")
    args = ap.parse_args()

    jar = args.jar.expanduser().resolve()
    if not jar.is_file():
        sys.exit(f"error: {jar} not found")

    with zipfile.ZipFile(jar) as z:
        names = z.namelist()
        if any(n.upper().startswith("META-INF/") and n.upper().endswith((".RSA", ".DSA", ".SF"))
               for n in names):
            sys.exit("error: jar is signed — editing it would break the signature")
        configs = [n for n in names if n.endswith(".mixins.json")]
        if args.list or not (args.config and args.mixin):
            print(f"mixin configs in {jar.name}:")
            for c in configs:
                d = json.loads(z.read(c))
                for section in ("mixins", "client", "server"):
                    for m in d.get(section, []):
                        print(f"  {c}  [{section}]  {m}")
            return
        if args.config not in names:
            sys.exit(f"error: {args.config} not in jar. Try --list.")
        data = json.loads(z.read(args.config))

    section = next((s for s in ("client", "server", "mixins")
                    if args.mixin in data.get(s, [])), None)
    if section is None:
        sys.exit(f"error: {args.mixin} not found in {args.config}. Try --list.")
    if section != "client":
        print(f"! {args.mixin} is in the '{section}' section, not 'client'.")
        print("  Removing a common/server mixin can change behaviour the server "
              "also relies on. Continue only if you know it is safe.")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = jar.with_suffix(jar.suffix + f".bak-{stamp}")
    shutil.copy2(jar, backup)
    print(f"backed up -> {backup.name}")

    data[section] = [m for m in data[section] if m != args.mixin]
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / args.config
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(data, indent=2), encoding="utf-8")
        # `zip` replaces the entry in place, leaving every other entry untouched
        r = subprocess.run(["zip", "-q", str(jar), args.config], cwd=td)
        if r.returncode != 0:
            shutil.copy2(backup, jar)
            sys.exit("error: repack failed; jar restored from backup")

    with zipfile.ZipFile(jar) as z:
        still = args.mixin in json.loads(z.read(args.config)).get(section, [])
        bad = z.testzip()
    if still or bad:
        shutil.copy2(backup, jar)
        sys.exit("error: verification failed; jar restored from backup")
    print(f"removed {args.mixin} from [{section}] in {args.config}")
    print("The mod's declared version is unchanged, so servers see it as before.")


if __name__ == "__main__":
    main()
