# Security and privacy

- The administration UI and API bind to `127.0.0.1`. Do not reverse proxy them onto the public Internet.
- LAN sharing is disabled by default and exposes only read-only, token-protected subscription downloads. It uses HTTP and is intended for a trusted private network.
- Subscription links grant access to YAML that may contain proxy credentials. Do not post them in issues, screenshots, logs or pull requests. Reset exposed tokens and upstream credentials.
- SQLite databases, backups and LAN settings are stored under `data/` by default. Theme and UI preferences are stored in the browser. Source URLs are fetched by the local backend; only import sources you trust.
- No software updater, telemetry or cloud storage is included. Dependencies are downloaded on initial setup. Source refreshes contact the configured subscription provider.
- Validation checks structure and references, not every protocol or Mihomo core capability.

For a security report, first open an issue containing only a brief, non-sensitive description and request a private reporting channel. Do not publish exploit details or credentials in an ordinary issue.
