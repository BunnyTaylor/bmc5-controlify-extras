# Publishing to Modrinth

## Project settings

Create the project once at <https://modrinth.com/dashboard> — it's quicker to
fill the licence, summary and gallery in there than over the API.

| Field | Value |
| --- | --- |
| Project type | **Resource pack** |
| Slug | `bmc5-controlify-extras` |
| Loader | `minecraft` (the only loader Modrinth allows for resource packs) |
| Game version | `1.21.1` |
| Categories | `modded`, `tweaks`, `utility` |
| Client / server | client **required**, server **unsupported** |
| Licence | MIT |
| Icon | `pack.png` in the repo root |

Modrinth has no dependency entry for Controlify's resource-pack hooks, so say
it in the summary instead: **requires Controlify**.

## Summary (limit 256 chars)

> Controller quality-of-life for Better MC 5: an 8-slot radial menu preloaded
> with the modpack's essentials (map, waypoints, backpack, accessories, quest
> book), paddle bindings, and fixes for GUIs Controlify can't navigate.

## Body

Reuse `README.md` — it's written to read as a listing page. Trim the *Install*
section down to "drop the zip in `resourcepacks/` and enable it", since people
downloading from Modrinth won't have the repo's installer. Keep the **note that
the virtual-mouse fix lives in `config/controlify.json`** rather than in the
pack, or Modrinth users will wonder why Xaero's map still isn't navigable.

## Publishing a version

```sh
export MODRINTH_TOKEN=mrp_...        # Settings -> PATs, scope: Create versions
scripts/publish-modrinth.py --project bmc5-controlify-extras --dry-run
scripts/publish-modrinth.py --project bmc5-controlify-extras
```

It uploads everything in `dist/`, with the main pack as the primary file and
the dragons add-on as a secondary. Bump `VERSION` first.

## Will it break on other modpacks?

No, and this is worth stating on the listing. Both failure modes degrade
quietly:

- A **radial action** naming a binding that doesn't exist logs
  `Binding {} does not exist or is not a radial candidate` and renders that
  slot empty (`RadialItems` falls back to `EMPTY_ACTION`).
- A **default bind** for an unregistered keybind is simply never looked up.

So on a pack without Xaero or Backpacked you get empty slots, not a crash. It's
still worth labelling the project as *for Better MC 5*, because that's the only
pack where every slot is populated.
