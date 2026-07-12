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
2. Install the "WhatsApp MCP" app.
3. Set the `mcp_auth_token` option (see below) before starting the app.
4. Start the app and open its **Log** tab. On first run a QR code is
   printed there - scan it with WhatsApp on your phone under
   **Settings > Linked Devices**. You have about 3 minutes before the QR
   code expires; restart the app to get a new one if it does.
   If the ASCII QR code in the log is hard to scan (common in browser-based
   log viewers), open a scannable image instead: in a browser, go to the
   *same address/IP you use for Home Assistant itself*, but with port 8082
   instead, and add `/qr.png` to the path - e.g. if Home Assistant is at
   `http://192.168.1.50:8123`, open `http://192.168.1.50:8082/qr.png`. Add
   `?token=<mcp_auth_token>` to that URL if you set the option. This only
   responds while a pairing QR is active; it 404s once you're paired.
5. Once paired, point your MCP client at port 8081 instead (again, same
   host/IP as Home Assistant, different port) - e.g.
   `http://192.168.1.50:8081/mcp` - with header
   `Authorization: Bearer <mcp_auth_token>`.

Re-authentication is only needed if you unlink the device from WhatsApp, or
after roughly 20 days of the app not running - not on every restart, since
session data persists on `/data`.

## Options

### `mcp_auth_token` (optional, but strongly recommended)

A bearer token that MCP clients must present to use the server:

```
Authorization: Bearer <mcp_auth_token>
```

If left empty, the MCP server starts anyway (a warning is logged), but
**anyone who can reach port 8081 on your network can read your WhatsApp
message history and send messages as you** - there is no other
authentication layer. Set a long, random token and do not expose this port
to the internet (e.g. via router port-forwarding).

## Network / Security notes

- Port **8081/tcp** (the MCP server) is a credential-bearing API: only
  reachable by devices/services you trust, ideally not exposed outside your
  LAN, and always with `mcp_auth_token` set.
- Port **8082/tcp** (the pairing QR code image) is gated by the same
  `mcp_auth_token`, passed as `?token=<mcp_auth_token>` in the URL. If you
  leave `mcp_auth_token` empty, this endpoint is also unauthenticated for as
  long as a pairing QR is active (a few minutes, typically only during first
  setup) - anyone who can reach it on your network during that window could
  load the QR code and potentially link their own device instead of yours.
  This isn't materially different from the existing risk of anyone with
  access to the app's Log tab seeing the same QR code as ASCII art; it just
  widens *who* can see it, from "logged into Home Assistant" to "on your
  LAN", while no token is set.
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
