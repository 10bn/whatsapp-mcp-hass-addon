# Changelog

## 1.1.0

- Serve the WhatsApp pairing QR code as a proper PNG image
  (`http://<home-assistant-host>:8082/qr.png`) in addition to the ASCII-art
  QR code printed to the log, which often renders unreadably in a
  browser-based log viewer (wrapped/mangled half-block characters). The
  image server starts immediately at bridge startup - unlike the main REST
  API, which only starts after a successful connection, too late to help
  with pairing - and is gated by the same `mcp_auth_token` (as a `?token=`
  query parameter) so it doesn't introduce an unauthenticated way to hijack
  pairing beyond what the existing log-viewer QR code already exposes.
- Expose the new port 8082 in `config.yaml`/`translations/en.yaml`, and pass
  `mcp_auth_token` into the bridge's run script (`WHATSAPP_QR_TOKEN`) so it
  can gate the endpoint.

## 1.0.1

- Fix `Client outdated (405) connect failure` on startup: the pinned
  `whatsmeow` dependency was from March 2025 and presented a WhatsApp Web
  protocol version WhatsApp's servers now reject. Bumped `whatsmeow` (and
  its transitive dependencies) to a current version, and updated the five
  call sites whose signatures gained a `context.Context` parameter
  (`client.Download`, `sqlstore.New`, `container.GetFirstDevice`,
  `client.GetGroupInfo`, `client.Store.Contacts.GetContact`).
- Bump the Dockerfile's Go builder stage from `golang:1.24-alpine` to
  `golang:1.25-alpine` to match the `go 1.25.0` directive the whatsmeow
  bump pulled into `go.mod` (avoids relying on an auto-downloaded
  toolchain during the image build).

## 1.0.0

- Package this project as an installable Home Assistant app (`config.yaml`,
  `Dockerfile`, s6-overlay service scripts for both the Go bridge and the
  Python MCP server, `repository.yaml`, translations).
- Add a `streamable-http` transport to the MCP server (`whatsapp-mcp-server`)
  alongside the existing stdio transport, since a persistent app service
  can't be spawned over stdio by a client process. Gate it behind an
  optional bearer token (`MCP_AUTH_TOKEN` / the app's `mcp_auth_token`
  option) - without a token the server logs a warning that it is reachable
  on the network without authentication.
- Make the WhatsApp bridge's storage directory (`WHATSAPP_STORE_DIR`) and
  port (`WHATSAPP_PORT`), and the MCP server's message database path
  (`WHATSAPP_MESSAGES_DB_PATH`) and bridge URL (`WHATSAPP_BRIDGE_URL`),
  configurable via environment variables so session data and message
  history can live on a persistent volume (`/data` inside the app).
- Bump the `mcp` Python dependency from 1.6.0 to >=1.9.0 (streamable-http
  support).
