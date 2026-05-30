# ALTTPR Follower Injector

Reskin the **Zelda follower** in *The Legend of Zelda: A Link to the Past* with any
community **ZSPR** sprite — the same sprites you'd drop onto Link in the randomizer.

Point it at a sprite and a ROM, hit **Update ROM**, and the Zelda who escorts you
from the castle to the sanctuary now looks like your character — walking, standing,
in her cell, and at the sanctuary — with a live preview of all four directions.

<!-- ![preview](docs/preview.png) -->

## Quick start

1. Download **`ALTTPRFollowerInjector.exe`** (Windows, standalone — no install needed).
2. Grab a `.zspr` sprite from **[alttp.mymm1.com/sprites](http://alttp.mymm1.com/sprites/)**.
3. Run the app → pick the sprite and your `.sfc` ROM → **Update ROM**.

> Windows may show a SmartScreen "unknown publisher" prompt the first time
> (the EXE is unsigned). Choose **More info → Run anyway**. The first launch is a
> second or two slower while the one-file EXE unpacks itself.

## Features

- **Any ZSPR sprite** — uses the standard randomizer sprite format.
- **Standalone Windows app** — no Python or install required.
- **Every follower state covered** — the walking follower (with its two-frame leg
  animation), the at-rest follower, Zelda in her cell, and Zelda standing in the
  sanctuary are all reskinned and recolored consistently.
- **Smart palette handling** — the follower is repointed to a free sprite palette so
  the sprite's colors don't bleed onto other NPCs. Palette and mail color
  (green / blue / red) are selectable.
- **Non-destructive** — always writes a *new* ROM; your original is untouched. Patches
  in place, so it works on vanilla JP 1.0 and A Link to the Past Randomizer ROMs.
- **Live preview** before you commit.

## How it works

This started as a "just swap the graphics" idea and turned into a small
reverse-engineering project:

- A from-scratch implementation of ALTTP's **LC_LZ2** graphics compression
  (decompress + recompress, validated round-trip against every sprite sheet).
- The follower's **draw routine** was decoded from the disassembly to map the exact
  tile layout — including the quirk that the side-facing walk alternates between two
  body frames (miss one and the legs drop every other step).
- The **sprite-palette loader** was mapped to find which OBJ palettes are static vs.
  per-area, so the follower could be moved to a free palette instead of the shared
  one Nintendo gave Zelda.
- The cell/sanctuary Zelda turned out to be a *separate sprite* that borrows the
  follower's graphics — so it's brought along by repointing one palette byte.

## Credits & attribution

- Built on the community Link sprite manifest from the
  [sprite-something](https://github.com/spannerisms/SpriteSomething) tool.
- Follower/sprite behavior was decoded against
  [spannerisms/jpdasm](https://github.com/spannerisms/jpdasm) (ALTTP JP 1.0 disassembly).
- ZSPR sprites and the sprite database are community resources.

## Disclaimer

Built for **A Link to the Past Randomizer** ROMs (JP 1.0 base). **No ROM is included** —
bring your own legally-obtained copy. Not affiliated with or endorsed by Nintendo.

## License

MIT — see [LICENSE](LICENSE).
