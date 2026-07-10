# Changelog

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
