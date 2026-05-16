# Cursor Concept

A modernized cursor theme package for Windows, based on the original work by [rosea92](https://www.deviantart.com/rosea92).

## Credits

- **Original cursor design**: [rosea92](https://www.deviantart.com/rosea92) / [Windows 11 Cursors Concept HD v2](https://www.deviantart.com/jepricreations/art/Windows-11-Cursors-Concept-HD-v2-890672103)
- **Previous distribution**: [PSGitHubUser1/Windows-11-Cursor-Concept-Pro-v2.0](https://github.com/PSGitHubUser1/Windows-11-Cursor-Concept-Pro-v2.0)
- This project is a **technical modernization** of the original cursor graphics. All cursor designs remain the intellectual property of their original authors.

See [Agreement.txt](./Agreement.txt) for the original author's terms.

## What's Different

| Aspect | Original | This Project |
|--------|----------|--------------|
| Installation | `.inf` + `.cmd` scripts | Modern Rust CLI installer (planned) |
| Theme management | Manual file copying | Automated theme switcher with backup/restore |
| Structure | Deep nested directories | Flat, version-controlled layout |
| Size | ~300MB+ (all variants) | ~98MB (dark small + light small only) |

## Themes

### Dark (Small)
- **Base**: 15 standard cursors
- **Variants**: 10 color schemes for animated cursors (busy/working)
  - default, classic, amber, green, indigo, red, squid, purple, candy, sunset

### Light (Small)
- Same structure as Dark

## Installation

> TODO: Rust installer is under development. For now, use the `.inf` files in each theme directory.

## License

The original cursor graphics are subject to the terms in [Agreement.txt](./Agreement.txt).  
The code and tooling in this repository are licensed under MIT.

## Roadmap

- [ ] Rust CLI installer (`cursor-cli install --theme dark --variant amber`)
- [ ] Theme preview GUI
- [ ] System tray quick switcher
- [ ] Auto-backup and restore default cursors
