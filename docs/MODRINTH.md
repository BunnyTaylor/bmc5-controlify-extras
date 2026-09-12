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
export MODRINTH_TOKEN=mrp_...   # scopes: Create versions AND Read projects
scripts/publish-modrinth.py --project bmc5-controlify-extras --dry-run
scripts/publish-modrinth.py --project bmc5-controlify-extras
```

**Both scopes matter.** The upload needs *Create versions*, but the script must
first turn the slug into a base62 id (`POST /v2/version` rejects a slug with
`Invalid character '-' in base62 encoding`), and that lookup needs *Read
projects*. A token with only *Create versions* gets 401 on `/v2/user` and 404
on the project — which is indistinguishable from the project not existing.

To avoid the read scope entirely, pass the **base62 id** instead of the slug;
the script detects an 8-character alphanumeric argument and skips the lookup:

```sh
scripts/publish-modrinth.py --project AbCdEfGh
```

A brand-new project is a **draft**: invisible to non-maintainers and to
unauthenticated lookups, and it cannot be submitted for review until it has at
least one version. So the order is create -> upload a version -> submit.

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
