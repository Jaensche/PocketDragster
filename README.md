# Pocket Dragster

A drag-racing game for the original Game Boy (DMG), built with GBDK-2020 4.5.0.

## Build

```sh
make            # -> build/pocketdragster.gb
make clean
make run        # opens the ROM in Emulicious (expects Emulicious/Emulicious.jar, which is not tracked; override with EMULICIOUS=...)
```

Cartridge header: MBC5 without RAM or battery (type 0x19), 32 KB ROM. 

## Layout

- `src/` – C sources and headers
- `res/` – generated assets (tiles/maps from png2asset), compiled automatically
- `build/` – ROM plus debug symbols (`.cdb`, `.noi`, `.map`)

## Debugging in VS Code

1. Install the **Emulicious Debugger** extension.
2. Start Emulicious and turn on *Tools → Remote Debugging → Enabled*. The port defaults to 58870.
3. Press F5 ("Debug in Emulicious"). This builds the ROM and attaches with C source-level breakpoints.
