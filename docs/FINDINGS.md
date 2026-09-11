# How this works — notes from decompiling Controlify 3.0.1

Everything below was read out of
`mods/controlify-3.0.1+lts+1.21.1-neoforge.jar` with `javap`, not from docs.
It's recorded here so the pack can be updated without re-deriving it.

## 1. Controlify's defaults come from the resource pack stack

`dev.isxander.controlify.bindings.defaults.DefaultBindManager` is a
`SimpleControlifyReloadListener` over the directory
`assets/<namespace>/controllers/default_bind/`. The matching
`DefaultConfigManager` covers `controllers/default_config/`.

Both are fed by the **client resource manager**, which means an ordinary
resource pack can supply them. Controlify ships its own proof of this: the
built-in `legacy_console` pack inside the jar overrides both files.

That's why this project is a resource pack and not a mod.

## 2. Bind layers merge, and a user pack wins

`readDefaults` walks the resource stack and **prepends** each layer:

```
78: aload_3
79: iconst_0                       // index 0
97: invokeinterface List.add:(ILjava/lang/Object;)V
```

`LayeredDefaultBindProvider.getDefaultBind` then returns the first non-null
layer. Resource stacks run low→high priority, so prepending puts the
highest-priority pack at index 0 — a pack enabled last overrides the built-ins.

A layer may also set `"clear_below": true`, which stops the search and leaves
anything it doesn't mention unbound. **This pack does not use it**, so it only
overrides the four paddle binds and leaves every other default alone.

Per-controller files (`steam_deck.json`, `switch.json`, …) are partial overlays:
`apply` appends the `default` namespace provider to the end of every other
namespace's layer list. Controlify's own `dualsense.json` is a single binding,
which is what tipped this off.

`default_config` merges differently but to the same effect — a recursive
`JsonObject` deep merge, so a partial file only overrides the keys it names.

## 3. Modded keybinds get predictable IDs

`ControlifyBindings.registerModdedBindings()`:

```
49: KeyMapping.getName()                    // the translation key
52: String.toLowerCase()
55: ldc "[^a-z0-9/._-]"
57: ldc "_"
59: String.replaceAll
62: String.trim
66: ldc "fabric-key-binding-api-v1"
69: ResourceLocation.fromNamespaceAndPath
```

So every modded keybind is registered as:

```
fabric-key-binding-api-v1:<translation key, lowercased, sanitised>
```

`gui.xaero_open_map` → `fabric-key-binding-api-v1:gui.xaero_open_map`. BMC5's
translation keys are already lowercase with only `.` and `_`, so they pass
through the sanitiser unchanged. The namespace is `fabric-…` on NeoForge too.

Each generated bind is marked `radialCandidate(...)`, which is what makes them
eligible for the radial menu.

On NeoForge the source list is `NeoforgePlatformClientImpl.calculateModdedKeyMappings()`
— `Options.keyMappings` minus the vanilla set captured by
`VanillaKeyMappingHolder`. Keybinds that already correlate to a native
Controlify binding are skipped, so vanilla actions aren't double-registered.

## 4. Defaults apply live, without "Reset All Binds"

`InputBindingImpl` — when `keepDefaultBindings` is false (the default), a
binding whose current input equals its default input is **removed** from the
saved profile:

```
15: getfield InputSettings.keepDefaultBindings
19: ifne ...                                  // skip if true
22: Input.equals(defaultInput())
35: BindingsSettings.bindings
46: invokeinterface Map.remove
```

Only *customised* binds are persisted; everything else resolves from the
default provider at load time. So installing the pack changes binds immediately
— no reset needed — while anything you rebound by hand keeps winning.

## 5. Available inputs

From `controlify.input.*` in `assets/controlify/lang/en_us.json`:

- Faces/shoulders/sticks/d-pad, `start`, `back`, `guide`
- `left_paddle_1`, `left_paddle_2`, `right_paddle_1`, `right_paddle_2`
- `misc_1` … `misc_6`, `touchpad_1`, `touchpad_2`
- Raw fallbacks `button/0` … `button/19`, `axis/0` … `axis/19`

The Steam Deck font mapping defines glyphs for all four paddles, so paddle
support is fully wired — it's only the Deck *driver* that's disabled
(see [STEAM-DECK.md](STEAM-DECK.md)).

`misc_1` is deliberately left alone: Controlify's `switch.json` already binds it
to screenshot, and 8BitDo pads are identified as `controlify:switch`.

## 6. Virtual mouse matching

`GlobalSettings.fromDTO` resolves each entry of `global.virtual_mouse_screens`
with `Class.forName`, and `VirtualMouseHandler` tests them with
`isAssignableFrom`. Two consequences:

- A **base class** covers all its subclasses. `xaero.lib.client.gui.ScreenBase`
  alone covers the world map, the waypoint list and the add-waypoint screen
  (`GuiMap` reaches it via `xaero.map.gui.ScreenBase`). It lives in the
  jar-in-jar `xaerolib-neoforge-1.21.1-1.7.1.jar`.
- Unknown names are **safely ignored** — the lambda catches
  `ClassNotFoundException` and returns `Stream.empty()` — so listing screens for
  mods you don't have costs nothing.

## 7. Radial geometry

`RadialMenuScreen` divides `6.2831855f` (2π) by `8.0f` and offsets by
`1.5707964f` (π/2): **8 slots, slot 0 at the top, running clockwise**. That's
the order of the `actions` array in `default_config/default.json`.
