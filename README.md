# BMC5 Controlify Extras

A drop-in resource pack (plus a small installer) that makes **Better MC 5
[NEOFORGE] v52** properly playable on a controller, without switching your
Steam controller profile to a keyboard-mapping layout.

Built and verified against the exact versions in the pack:
Minecraft **1.21.1**, NeoForge **21.1.234**, Controlify **3.0.1+lts**.

## What it fixes

| Problem | Fix |
| --- | --- |
| No buttons left for modpack actions | An 8-slot **radial menu** preloaded with the BMC5 essentials — map, waypoints, backpack, accessories, ender chest, ping |
| Extra/back buttons unbindable | **Paddle bindings** for controllers that expose them (8BitDo Ultimate 2, Xbox Elite, …) |
| Xaero's map & FTB Quests unusable with a stick | Those screens added to Controlify's **virtual mouse** list |
| Steam Deck back buttons do nothing | Explained + worked around — see [docs/STEAM-DECK.md](docs/STEAM-DECK.md) |

Nothing here is a Java mod. It's a resource pack, because Controlify reads its
default bindings and default profile out of the **resource pack stack** — so a
pack can ship binds for keybinds belonging to *other* mods. Details and the
decompiled evidence are in [docs/FINDINGS.md](docs/FINDINGS.md).

## Install

```sh
scripts/install.py "<instance folder>"             # desktop / 8BitDo
scripts/install.py "<instance folder>" --deck      # Steam Deck (see below)
scripts/install.py "<instance folder>" --dragons   # + Dragon Mounts add-on
```

Add `--dry-run` first if you want to see the changes without writing anything.
Point it at the instance folder or its inner `minecraft/` dir — either works.

Prism (Flatpak) instances live under:

```
~/.var/app/org.prismlauncher.PrismLauncher/data/PrismLauncher/instances/
```

The installer builds `dist/BMC5-Controlify-Extras.zip`, copies it into
`resourcepacks/`, enables it **last** in `options.txt` (so its Controlify
defaults win over every other pack), and adds the virtual-mouse screen classes
to `config/controlify.json`. Every file it edits is backed up alongside the
original as `*.bak-<timestamp>`.

Prefer to do it by hand? Drag `dist/BMC5-Controlify-Extras.zip` into
`resourcepacks/` and enable it in **Options → Resource Packs**. You'll just
miss the virtual-mouse fix, which lives in the global config rather than the
pack.

## The radial menu

Press **D-Pad Right** (Controlify's default) and flick the **right stick**:

```
                     ↑   Xaero World Map
   Waypoint List ↖         ↗   Accessories Screen
    New Waypoint ←    ( ● )    →  Open Backpack
           Ping  ↙         ↘   Ender Chest
                     ↓   Quest Book
```

The four most-used actions sit on the cardinal directions, which are far easier
to hit than the diagonals. **Open Backpack** is the Backpacked keybind, so it
opens the pack you're *wearing* — no unequipping, no hotbar shuffle.

**Quest Book** is FTB Quests' `Open Quests`, which ships **unbound** in BMC5 —
so in a quest-driven pack the quest log had no key at all, on controller *or*
keyboard. Its screen is an `ftblibrary.ui.BaseScreen`, which the installer
already adds to the virtual-mouse list, so it's navigable once opened.

## Paddles

If your controller exposes paddles, these are bound automatically:

| Paddle | Action |
| --- | --- |
| L4 (`left_paddle_1`) | Zoom — hold (JustZoom) |
| L5 (`left_paddle_2`) | Vein mining — hold |
| R4 (`right_paddle_1`) | Open backpack |
| R5 (`right_paddle_2`) | Open world map |

Zoom and vein mining are *holds*, which a radial menu can't do — that's why
they live on paddles. Map and backpack are on paddles **as well as** in the
radial, because they're frequent enough to deserve an instant button.

**Vein Mining was inert before this.** Its config sets
`activationState = "HOLD_KEY_DOWN"` while the keybind shipped unbound, so the
mod could not be triggered at all — the mod's own warning string is *"Vein
mining key is unbound, set a key binding to enable controls."* Binding a paddle
fixes it. On a pad with no paddles, bind it in Controlify by hand or give it a
key in Options → Controls; the radial can't host it because it's a hold.

**8BitDo Ultimate 2 Wireless:** SDL only ships paddle mappings for this pad on
Windows/macOS — there is no Linux entry in Controlify's bundled database, only
for the *Ultimate 2C*. On Linux the paddles may arrive as raw numbered buttons
instead. If they don't respond, open Controlify's bind screen and press one; if
it shows up as `Button #17` or similar, bind it there by hand. Also make sure
the paddles aren't set to *duplicate* a face button in 8BitDo's Ultimate
Software — set them to their own dedicated outputs, or SDL sees the face button.

**Steam Deck:** the back buttons cannot reach Controlify at all in 3.0.1.
See [docs/STEAM-DECK.md](docs/STEAM-DECK.md) for why, and for the Steam Input
workaround that `--deck` sets up.

## Optional: Dragon Mounts add-on

Dragon Mounts Remastered ships `Descend`, `Dismount` and `Dragon Command Menu`
unbound, and there are no buttons left. The add-on pack exploits the fact that
**two Controlify bindings may share one input** — the config screen only paints
sharers red, it never blocks them, and at runtime both fire.

That only *helps* when the two actions can't both be live. `Call Dragon` works
when you're on foot; `Descend` works when you're flying one. They're mutually
exclusive in the mod's own logic, so they can share a paddle safely:

| Input | On foot | While riding |
| --- | --- | --- |
| R5 (`right_paddle_2`) | Call Dragon | Descend |

It frees R5 by unbinding the world map there (`"type": "empty"`) — the map is
still radial slot 0, so nothing is actually lost. Install with `--dragons`; it
loads *after* the main pack, so its overrides win.

**Don't pair `Descend` with jump.** Jump is ascend while mounted, so they'd
fight each other — the pairing has to be foot-state against flight-state, not
two flight actions. `Dismount` needs no binding at all: vanilla sneak already
dismounts.

## Customising

Everything is editable in-game: **Controlify settings → your controller →
Radial Menu → CONFIGURE**, and the bind list right below it. Any bind you
change by hand is saved to your profile and from then on overrides this pack.

To change the defaults instead, edit
`pack/assets/controlify/controllers/default_config/default.json` (radial slots,
in clockwise order from the top) or `default_bind/default.json` (paddles), then
re-run the installer.

Binding IDs for other mods follow a fixed rule — Controlify registers every
modded keybind as:

```
fabric-key-binding-api-v1:<the keybind's translation key>
```

So `gui.xaero_open_map` becomes
`fabric-key-binding-api-v1:gui.xaero_open_map`. Translation keys are the
`key_*` entries in the instance's `options.txt`. (The `fabric-` namespace is
not a typo — Controlify uses it on NeoForge too.)

## Modrinth

Both packs are built into `dist/` ready to upload. See
[docs/MODRINTH.md](docs/MODRINTH.md) for the project settings, listing copy and
the publish script.

On a modpack without these mods nothing breaks: a radial slot naming a missing
binding logs a warning and renders empty, and a default bind for an
unregistered keybind is never looked up.

## Uninstall

Disable the pack in **Options → Resource Packs**, or delete
`resourcepacks/BMC5-Controlify-Extras.zip`. To revert the config edits, restore
the `.bak-<timestamp>` files the installer left next to `options.txt` and
`config/controlify.json`.
