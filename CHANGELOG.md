# Changelog

## 0.4.1 (2026-10-22)

- Add English UI, automatic browser-language detection and a persistent language selector.
- Translate controls, dialogs, notifications, accessibility labels and application diagnostics while preserving user YAML and names.
- Add Windows x64, Linux x64/ARM64 and macOS Intel/Apple Silicon native build targets with bundled Python, dependencies, frontend and corresponding source.
- Add cross-platform launch/stop commands, persistent per-user native data paths, migration guidance and English project statements/credits.
- Promoted to a stable release at the maintainer's request. Five platform builds succeeded; Linux/macOS physical-device acceptance has not been established. No new automated functional tests were run in this iteration.

## 0.4.0-rc.1

First open-source release candidate. User acceptance confirmed and published on 2026-10-22. The uploaded ZIP is unchanged from the tested candidate.

- Import Clash / Mihomo YAML from URL, local file or built-in example.
- Edit nodes, proxy groups and routing rules, then publish a token-protected subscription.
- Keep edits when refreshing upstream; support preview and version history.
- Optional read-only LAN subscription server, separate from loopback-only administration.
- AI routing preset including Muse AI; 24 services and 67 domain rules.
- Five color presets and six custom colors, saved in the current browser.
- GPL-3.0-only license, third-party notices, clean packaging and SHA-256 manifest.

This package includes source and built frontend, not a standalone Windows executable.
