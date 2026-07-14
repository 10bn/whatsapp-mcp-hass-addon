# Changelog

## 1.3.1

- Fix slow/hanging queries on broad message sweeps (e.g. "summarize the
  last 60 days"): the `messages` table had no indexes beyond its primary
  key (`id, chat_jid`), so every `list_messages`/`get_message_context`
  query - which filters/sorts by `timestamp` and filters by `chat_jid`/
  `sender` - was a full table scan plus an in-memory sort, worsening as
  history grows. Added indexes on `messages(timestamp)`,
  `messages(chat_jid, timestamp)`, and `messages(sender)`. Verified with a
  60k-row synthetic dataset: the query plan changes from `SCAN messages` +
  `USE TEMP B-TREE FOR ORDER BY` to an indexed range search, ~280x faster
  in that test (0.028s -> 0.0001s).
- Enable SQLite WAL mode (plus a 5s busy timeout) on the bridge's message
  database, so the MCP server's long reads don't contend for the same lock
  as the bridge's own continuous writes (new incoming messages).

## 1.3.0

- Fix a pre-existing bug (inherited from upstream, not introduced by the app
  packaging) where several MCP tools returned data that didn't match their
  declared output schema, causing FastMCP/pydantic to reject the response
  outright: `list_chats`, `search_contacts`, `get_chat`,
  `get_direct_chat_by_contact`, and `get_contact_chats` returned raw
  dataclass instances where a plain dict was declared; `list_messages`
  returned a single pre-formatted string where a list of message objects
  was declared (and expected). Added a `_jsonable()` converter in
  `main.py` and made `whatsapp.list_messages()` actually return structured
  `Message` objects; removed the now-dead `format_messages_list()`.
- Fix a related, separately-discovered bug affecting stdio transport
  (Claude Desktop/Cursor usage): several error-handling paths in
  `whatsapp.py` called `print()`, which writes to stdout - the same stream
  the stdio MCP transport uses for the JSON-RPC protocol, so any error
  during a tool call could corrupt the connection. Redirected all of them
  to stderr.
- Add `list_newsletters` and `unfollow_newsletter` MCP tools, backed by
  whatsmeow's `GetSubscribedNewsletters`/`UnfollowNewsletter` APIs via two
  new bridge REST endpoints (`GET /api/newsletters`,
  `POST /api/newsletter/unfollow`), so channels/newsletters can be listed
  and unsubscribed from directly.

## 1.2.0

- Secure by default, matching the pattern used in this author's other MCP
  apps (e.g. `ssh-mcp-hass-addon`): the app now auto-generates a random
  128-bit secret on first start and persists it under `/data`, instead of
  starting fully open when `mcp_auth_token` is left empty. Both the MCP
  server (8081) and the pairing QR image (8082) are gated by this shared
  secret.
- Add a `/private_<secret>` URL form for the MCP server, equivalent to the
  existing `Authorization: Bearer <secret>` header, for MCP clients that
  can only be pointed at a bare URL. An unknown secret on that path gets a
  plain 404 rather than a 401, so it doesn't confirm the path is
  meaningful.
- Add a `disable_auth` option to explicitly opt back into the old
  fully-open behavior, for users who want it on a fully trusted network.
- Use constant-time comparison for all secret checks (Python
  `hmac.compare_digest`, Go `crypto/subtle.ConstantTimeCompare`), and 404
  (not 401) invalid QR-image tokens too, for consistency.
- Both services' `run` scripts now log a ready-to-use URL (with the
  resolved secret already filled in) for the MCP endpoint and the pairing
  QR image, instead of the token being left as a placeholder.

## 1.1.1

- Fix confusing QR-image instructions: the log/docs literally printed
  `http://<home-assistant-host>:8082/qr.png`, which reads like a real
  (broken) URL rather than a placeholder to substitute, and users
  reasonably tried to open it verbatim. Replaced with explicit
  instructions to reuse the same host/IP as the Home Assistant UI on a
  different port, plus a concrete worked example
  (`http://192.168.1.50:8082/qr.png`), in the bridge's log output, the
  README, and DOCS.md.
- Log a confirmation line when the QR image server starts listening, to
  make it easier to tell "not reachable" apart from "never started".

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
