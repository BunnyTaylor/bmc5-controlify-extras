# Steam Deck back buttons (L4/L5/R4/R5)

## Why they don't work

Controlify reads the Deck's back buttons through its *enhanced Steam Deck
driver*. In **Controlify 3.0.1+lts** that driver is switched off in code.
Decompiling `dev/isxander/controlify/driver/steamdeck/SteamDeckUtil.class`:

```
private static boolean isHardwareSteamDeck();
   0: getstatic     LOGGER
   3: ldc           "Skipping Steam Deck checks as steamOS has temporarily broken the enhaned driver."
   5: invokeinterface ControlifyLogger.error
  10: iconst_0
  11: ireturn          // returns false, unconditionally
```

It returns `false` no matter what. `IS_STEAM_DECK` is therefore never set, the
Deck driver never starts, and Controlify falls back to seeing your Deck as an
ordinary SDL gamepad — sticks, triggers and face buttons only.

Controlify's own warning text spells out what that costs:

> Controlify requires Decky Loader to be installed on your Steam Deck to be able
> to use the enhanced Steam Deck driver. […] You can use Controlify without, but
> you will lose access to: **back-buttons**, touchpads, gyro, auto game pause,
> screenshot integration.

So this is **not** something you configured wrong, and installing Decky Loader
will not help while the driver is disabled. No resource pack or add-on mod can
reach those buttons either — the input never arrives.

The radial menu is the real answer here: it puts all eight modpack actions on
**D-Pad Right + right stick**, needs no back buttons, and works identically on
the Deck and on a desktop pad.

## If you still want the back buttons: Steam Input

Steam Input can read the back buttons even when Controlify can't, and send them
as keyboard keys. The trick is to add *only* the back buttons and leave the rest
of the layout as a normal gamepad — so Controlify still sees a controller for
everything else. This is not the same as switching to a full keyboard-mapped
layout.

Run the installer on your Deck's instance with `--deck`:

```sh
scripts/install.py "<instance folder>" --deck
```

That moves three actions onto the only unused single letters in BMC5 —
`g`, `j`, `n`, verified against all 218 keybinds. The world map is left alone:
it already sits on `m`, the sole binding using that key.

| Key | Action | Keybind change |
| --- | --- | --- |
| `G` | Zoom (hold) | moved off `z`, which three mods share |
| `J` | Vein mining (hold) | was unbound entirely |
| `N` | Open backpack | moved off `b`, which five mods share |
| `M` | Open world map | none — already unique |

**Letters rather than the numpad.** With NumLock off the OS sends navigation
keysyms instead of `KP_*`, and a Deck driving a virtual keyboard through Steam
Input is exactly where that goes wrong. Letters have no such ambiguity.

Then, in **Gaming Mode** (not Desktop Mode):

1. Launch Prism → gamepad icon → **Controller Settings**.
2. Keep the existing gamepad template. Don't switch to a keyboard layout.
3. **Back Grip Buttons** → assign, leaving every other input untouched:
   - L4 → `G`
   - L5 → `J`
   - R4 → `N`
   - R5 → `M`

Why move them off their defaults? In BMC5 `B` is bound by
five different mods at once (Backpacked, Xaero's new-waypoint, Inmis, Tom's
Storage, Deeper Darker) and `Z` by three. A keyboard key fires *every* mod bound
to it, so pressing `B` would open a backpack *and* drop a waypoint. Controlify's
own binds don't have this problem — it presses each mod's keybind object
directly rather than faking a key — which is why this remap is only needed for
the Steam Input route.

## Gaming Mode matters

Controlify also warns:

> It is essential to switch to Gaming Mode on your Steam Deck. […] Desktop mode
> attempts to convert your Deck input into a keyboard and mouse.

Launch the game from Gaming Mode. In Desktop Mode the Deck emulates mouse and
keyboard and Controlify may not see a controller at all.

## Worth re-checking later

The driver is disabled pending a SteamOS fix, not removed. If a later Controlify
release restores it, the back buttons become bindable natively as
`left_paddle_1/2` and `right_paddle_1/2` — the pack already binds those four,
so they'd start working with no changes. You could then revert the `--deck`
keybind remap from the `options.txt` backup.
