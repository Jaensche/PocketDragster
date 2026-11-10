# Quarter Mile (working title)

A drag-racing game for the original Game Boy (DMG), built with GBDK-2020 4.5.0.

GBDK is not tracked in git. Download the Linux release from https://github.com/gbdk-2020/gbdk-2020/releases and unpack it to `gbdk/` in the repo root, or set `GBDK_HOME`.

## Build

```sh
make            # -> build/quartermile.gb
make clean
make run        # opens the ROM in Emulicious (expects Emulicious/Emulicious.jar, which is not tracked; override with EMULICIOUS=...)
```

Cartridge header: MBC5 + RAM + battery (type 0x1B), 32 KB ROM, 8 KB SRAM (for best times).

## Layout

- `src/` – C sources and headers
- `res/` – generated assets (tiles/maps from png2asset), compiled automatically
- `build/` – ROM plus debug symbols (`.cdb`, `.noi`, `.map`)

## Debugging in VS Code

1. Install the **Emulicious Debugger** extension.
2. Start Emulicious and turn on *Tools → Remote Debugging → Enabled*. The port defaults to 58870.
3. Press F5 ("Debug in Emulicious"). This builds the ROM and attaches with C source-level breakpoints.
