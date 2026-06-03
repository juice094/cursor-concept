# Cursor Concept

Windows 光标主题包，提供黑白两套高对比度指针方案。

- **Dark**：深色光标，适合浅色背景 / 日间使用
- **Light**：浅色光标，适合深色背景 / 夜间使用

基于 [rosea92](https://www.deviantart.com/rosea92) 的原始设计整理。光标图形版权归原作者，见 [Agreement.txt](./Agreement.txt)。

## Contents

```
themes/
├── dark/
│   ├── base/          # 15 static cursors (.cur)
│   └── 01_default/    # busy.ani + working.ani
└── light/
    ├── base/          # 15 static cursors (.cur)
    └── 01_default/    # busy.ani + working.ani
```

**Base cursors**: `pointer`, `help`, `precision`, `handwriting`, `unavailable`, `vert`, `horz`, `dgn1`, `dgn2`, `move`, `alternate`, `link`, `beam`, `pin`, `person`

## Installation

Requires **PowerShell 7+** (`pwsh`).

```powershell
# Install dark theme (default)
pwsh -File .\install.ps1

# Install light theme
pwsh -File .\install.ps1 -Light

# Restore system default cursors
pwsh -File .\install.ps1 -Restore
```

No Administrator privileges required — files are copied to a local `installed/` directory and only `HKCU` registry keys are modified.

### Manual (INF)

Right-click `themes/dark/01_default/Install.inf` or `themes/light/01_default/Install.inf` → **Install**.

## Technical Notes

`scripts/extract_ani_frames.py` parses Windows `.ani` RIFF containers and extracts frame sequences + metadata. Verified: 40/40 files parsed successfully.

Windows 11 does not natively support SVG/PNG/GIF cursors — `.cur`/`.ani` remains the only system-level format.

## License

This repository contains two distinct classes of material with different licenses:

### Cursor Graphics (`themes/`)

Original designs by [rosea92](https://www.deviantart.com/rosea92). Subject to the terms in [Agreement.txt](./Agreement.txt):

- ✅ **Allowed**: Personal use on any compatible device; modification for personal use.
- ❌ **Not allowed**: Claiming ownership; using monetized URL shorteners linking to the original.
- ⚠️ **Distribution**: Publishing a heavily modified version requires the author's permission and clear attribution with a link to the DeviantArt page.

This distribution is a **structural reorganization** of the original pack (directory flattening, installer script, documentation). The cursor graphics themselves are unmodified. Attribution is provided above and in `Agreement.txt`.

### Code and Tooling (`install.ps1`, `build-release.ps1`, `scripts/`, etc.)

Licensed under the **MIT License**. You may copy, modify, and redistribute the installation scripts freely.
