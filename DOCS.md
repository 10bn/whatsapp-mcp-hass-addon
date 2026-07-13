# WhatsApp MCP - App documentation

This app packages both halves of this project into a single Home Assistant
app:

- **whatsapp-bridge** (Go): connects to WhatsApp via the whatsmeow
  multidevice web API, stores your message history in SQLite on the
  persistent `/data` volume, and exposes an internal REST API on port 8080
  (container-local only, not published to the network).
- **whatsapp-mcp-server** (Python): the MCP server. Inside this app it runs
  over **streamable-http** instead of stdio, so it can be reached by an MCP
  client anywhere on your network, on port 8081.

The Go bridge also serves the WhatsApp pairing QR code as a PNG image on
port 8082 while a pairing is in progress, as an alternative to the ASCII-art
QR code printed to the log (which often renders unreadably in a
browser-based log viewer, depending on font/line-height).

Both processes run continuously under s6-overlay for as long as the app is
started.

## Installation

1. Add this repository to your Home Assistant instance (Settings > Add-ons
   \> App store > ⋮ > Repositories), or use the badge in the main
   [README](./README.md).
2. Install the "WhatsApp MCP" app and start it - no configuration is
   required to get a secured setup; see [Options](#options) below only if
   you want a stable/fixed secret instead of the auto-generated one.
3. Open the app's **Log** tab. On first run a QR code is printed there -
   scan it with WhatsApp on your phone under **Settings > Linked Devices**.
   You have about 3 minutes before the QR code expires; restart the app to
   get a new one if it does.
   If the ASCII QR code in the log is hard to scan (common in browser-based
   log viewers), the log also prints a ready-to-use URL for a scannable PNG
   instead - copy it as-is, just replacing the host with your own Home
   Assistant address. It only responds while a pairing QR is active; it
   404s once you're paired (including for a *wrong* secret, so it never
   confirms the endpoint exists to someone without it).
4. Once paired, the log also prints a ready-to-use, no-header MCP URL - copy
   it (with the host replaced) straight into your MCP client. See
   [Connecting an MCP client](#connecting-an-mcp-client) for the header-based
   alternative.

Re-authentication is only needed if you unlink the device from WhatsApp, or
after roughly 20 days of the app not running - not on every restart, since
session data persists on `/data`.

## Options

### Auto-generated secret (recommended: leave both options below empty)

By default, the app generates a random 128-bit secret on first start and
persists it under `/data` - it survives restarts and updates, and both the
MCP server and the pairing QR image are gated by it. After starting the
app, open its **Log** tab and look for a line like:

```
No-header MCP URL: http://<home-assistant-host>:8081/private_5iBENz4JEcUW2X-QGVUMQw
```

Copy that URL (with `<home-assistant-host>` replaced by your own address)
straight into your MCP client - no header configuration needed.

- `mcp_auth_token` (optional): pin a fixed secret instead of the
  auto-generated one, e.g. if you want the URL to stay predictable across a
  fresh install.
- `disable_auth` (optional, default off): turns off the secret entirely,
  making both the MCP server and the pairing QR image reachable by anyone
  who can reach this app's ports on your network, with **no credential at
  all**. Only turn this on if you fully trust your network.

## Connecting an MCP client

There are two equivalent ways to authenticate, depending on what your
client supports - `8081` below is the app's default port; if you remapped
it on the app's **Network** tab, use that port instead (also shown in the
Log tab).

**With a header** - point the client at the fixed path and send the secret
as a bearer token:

```
http://<home-assistant-host>:8081/mcp
Authorization: Bearer <secret>
```

**With a URL only** - no custom header required, the secret is embedded in
the path instead (same idea as Home Assistant's own `/api/webhook/<id>`
URLs). Use this for clients/tools that only let you paste in a URL:

```
http://<home-assistant-host>:8081/private_<secret>
```

An unknown secret on this path gets a plain `404` (it doesn't reveal that
`/private_` is meaningful), so keep the full URL as secret as you would a
password.

## Network / Security notes

- Port **8081/tcp** (the MCP server) is a credential-bearing API: only
  reachable by devices/services you trust, ideally not exposed outside your
  LAN. Secured by the shared secret above unless you set `disable_auth`.
- Port **8082/tcp** (the pairing QR code image) is gated by the same
  secret, passed as `?token=<secret>` in the URL (the log prints the full
  URL for you). If `disable_auth` is set, this endpoint is also
  unauthenticated for as long as a pairing QR is active (a few minutes,
  typically only during first setup) - anyone who can reach it on your
  network during that window could load the QR code and potentially link
  their own device instead of yours.
- Port 8080 (the Go bridge's internal REST API used for sending/downloading
  messages) is intentionally **not** exposed by this app - it has no
  authentication of its own and is only meant to be called by the MCP
  server inside the same container.
- WhatsApp session credentials and your full message history (including
  media metadata) are stored unencrypted in SQLite under `/data/store`. This
  data is only as safe as your Home Assistant host and backups.
- As with any MCP server, this is subject to the
  ["lethal trifecta"](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/):
  an LLM agent with access to both your WhatsApp data and other tools could
  be tricked (e.g. via a malicious incoming message) into exfiltrating data.
  Review what the agent does with these tools before trusting it broadly.

## Sending and receiving files

- To send a file, `media_path` must point to a file the *container* can
  read. This app maps Home Assistant's `/share` folder in read-write mode,
  so files placed in `/share` on your HA instance are reachable at
  `/share/<filename>` from your MCP client's perspective (pass that path as
  `media_path`).
- Downloaded media (via `download_media`) is written under `/data/store`
  inside the container, which is not shared over the network. If you need
  to retrieve a downloaded file from outside the container, copy it into
  `/share` first (not currently automated).

## Storage & persistence

WhatsApp session credentials and the message/chat SQLite databases live at
`/data/store`, which Home Assistant persists across app restarts and
updates automatically - no extra volume mapping is required.

## Troubleshooting

See the main [README](./README.md#troubleshooting) for general
authentication and sync troubleshooting; it applies unchanged to the app
(the log tab replaces the terminal for the QR code).
