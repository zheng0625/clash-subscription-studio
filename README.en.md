# Clash Studio · Local Subscription Workspace

[简体中文](README.md) | **English**

A local visual editor and subscription server for Clash / Mihomo. Manage proxy nodes, groups and routing rules in one workspace, reapply your edits when the upstream subscription refreshes, and serve the published result to this computer or devices on your LAN.

**Next version: v0.4.1-rc.1 — bilingual UI and native packages, awaiting candidate acceptance.**

[Published releases](https://github.com/zheng0625/clash-subscription-studio/releases) · [Source repository](https://github.com/zheng0625/clash-subscription-studio) · [Native package guide](docs/native-packages.md#english)

## Features

- Import from a subscription URL, YAML file or built-in demo.
- Rename/exclude nodes, change proxy group policies and members, add/search/reorder routing rules.
- Preview drafts separately from published YAML. Keep edits across source refreshes and restore version history.
- Generate random-token subscription links, disable subscriptions or rotate their tokens.
- Create an AI routing preset with 24 services and 67 domain rules, including Muse AI.
- Share read-only subscriptions over your LAN while keeping administration on loopback.
- Choose five appearance presets or customize six colors.
- Switch between Simplified Chinese and English, follow your browser language automatically, or save a manual choice.
- Native Windows, Linux and macOS packages bundle Python, backend dependencies and the built frontend.

## Visual editing that survives source refreshes

The original configuration and your edits are stored separately. Rename or exclude nodes, organize groups and reorder rules in the UI. Refreshing the upstream configuration reapplies your edits. Validation conflicts keep the last published configuration available. Draft previews, explicit publishing and version history make changes easier to review.

![Clash Studio workspace with proxy groups and subscription publishing](docs/images/overview.png)

## Service-specific routing for Claude and other AI services

The AI preset matches exact domains and domain suffixes and routes them through an AI policy group. Claude / Anthropic entries include `anthropic.com`, `claude.ai`, `claude.com` and `claudeusercontent.com`. Preset rules precede ordinary rules and consolidate matching domains into the AI group, helping reduce inconsistent outbound choices caused by conflicting or missing rules.

For a consistent egress IP, choose a stable individual node and inspect the client's actual rule matches. Automatic latency selection, failover and other switching groups can change the outbound node. Even an individual node's upstream IP can change.

This manages routing rules; it does not guarantee complete coverage of future service domains or prevent unusual-IP detection, account restrictions or bans. Node IPs, client mode, DNS, region and platform policies also affect the outcome.

## AI routing in one step

Select an outbound policy to create a draft; save it to publish. Refreshing the source reapplies the preset, and repeating the action does not duplicate groups or rules. Disabling the preset restores ordinary rules. Chinese AI services and shared login/payment/general CDN domains retain their existing routing.

![AI preset: select an outbound policy and review the rule list](docs/images/ai-routing.png)

## Local processing and LAN distribution

Configuration, edits and version history stay on your computer. You do not need to send the subscription to a third-party conversion service. Clients retrieve the published YAML using its token-protected link. Optional LAN sharing lets phones, computers or routers on the same trusted network read it. The administration interface remains local only. Keep the computer and application running for subscription updates.

## Custom appearance

Choose Monochrome, Forest, Mist blue, Warm sand or Midnight. Customize the accent, page/card backgrounds, text and sidebar colors with live preview and automatic browser-local persistence.

![Appearance presets and custom colors](docs/images/themes.png)

These screenshots use an isolated demo configuration and contain no real subscription or working proxy credentials. They show the Chinese interface; v0.4.1 also offers English. Example nodes cannot provide a real proxy connection.

## Download and run

Choose the native archive matching your OS and CPU, then extract the complete directory:

| Platform | Start | Stop |
| --- | --- | --- |
| Windows 10/11 x64 | `ClashStudio.exe` or `Start.cmd` | `Stop.cmd` |
| Linux x64 / ARM64 | `./Start.sh` | `./Stop.sh` |
| macOS Intel / Apple Silicon | `ClashStudio.app` or `Start.command` | `Stop.command` |

Native packages include the interpreter, backend dependencies, prebuilt frontend and corresponding project source. No separate Python/Node.js installation or first-run dependency download is needed. A supported OS and an available web browser are required. Do not remove the bundled directories. The default UI URL is `http://127.0.0.1:8765`.

Use the language selector at the top right for Auto language, Simplified Chinese or English. Auto follows the browser's preferred language; a manual selection is remembered. Language changes do not rename nodes/groups or rewrite your YAML.

macOS packages are not Developer ID signed or Apple-notarized. Linux packages require a compatible glibc-based distribution. See [platform baselines and migration instructions](docs/native-packages.md#english). CI build success is not a claim of validation on every physical device. Native workflow artifacts are candidates; publishing a release remains a separate acceptance step.

## Source development

Source packages and GitHub source archives require Python 3.11+ and, when rebuilding the interface, Node.js 20.19+ / 22.12+ with npm or pnpm. On Windows use `启动软件.cmd` / `停止服务.cmd`, or `start.ps1` / `stop.ps1`; on Linux/macOS use `bash start.sh` / `bash stop.sh`.

Build the frontend with `pnpm install --frozen-lockfile` and `pnpm build` in `frontend/`. Install `requirements.txt` in a Python virtual environment and run `python run.py`. For native builds, install `requirements-build.txt` and run `python scripts/build_native.py` on the target OS and architecture.

## Storage and security

Source mode stores data in `data/`. Native mode uses `%LOCALAPPDATA%\ClashStudio` on Windows, `~/Library/Application Support/ClashStudio` on macOS, and `${XDG_DATA_HOME:-~/.local/share}/clash-studio` on Linux. `--data-dir` or `CLASH_STUDIO_DATA` can override this. Browser storage contains UI preferences, language and the selected subscription ID. Data is not automatically uploaded to GitHub.

Administration binds to `127.0.0.1:8765`. Optional LAN sharing uses a separate read-only HTTP port (8767 by default), disabled initially. Treat subscription links as credentials: their YAML may contain proxy secrets. Share only on trusted private networks and do not expose the service to the Internet. Source refreshes contact the configured provider.

## Developers and AI-assisted development

**zheng0625 initiated and leads this project, with OpenAI Codex assisting development.** Codex contributed throughout implementation, interface iteration, debugging, documentation and release preparation.

| Contributor | Contributions |
| --- | --- |
| [zheng0625](https://github.com/zheng0625), project initiator and maintainer | Requirements, product direction, feature and UI feedback, real-world acceptance testing and publication decisions. |
| OpenAI Codex, AI development assistant | Assisted architecture and frontend/backend implementation, appearance changes, debugging and fixes, test-case authoring and development-stage checks, documentation, packaging and publication workflows. |

Codex is a development tool; the maintainer remains responsible for project maintenance and release decisions. AI involvement does not mean the software is defect-free. Issues and pull requests are welcome.

## Scope and license

Clash Studio does not provide proxy nodes, accounts or subscriptions and does not handle proxy traffic. It is not a Clash/Mihomo core. Structure/reference validation does not replace core compatibility checks. Not every protocol, rule semantic or external provider feature is supported. Automatic source refresh requires the service to remain running.

Copyright (C) 2026 zheng0625 and contributors. Original project code is licensed under **GPL-3.0-only**, without warranty. See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Third-party components retain their own licenses. Native packages include corresponding project source and dependency notices.

[Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Changelog](CHANGELOG.md) · [Architecture](docs/architecture.md)
