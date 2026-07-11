ARG BUILD_FROM=ghcr.io/home-assistant/base:3.23

# ------------------------------------------------------------------
# Stage 1: compile the Go WhatsApp bridge (go-sqlite3 needs CGO, so we
# build on musl/Alpine to stay ABI-compatible with the HA base image).
# ------------------------------------------------------------------
FROM golang:1.25-alpine AS bridge-builder

RUN apk add --no-cache gcc musl-dev

WORKDIR /src
COPY whatsapp-bridge/go.mod whatsapp-bridge/go.sum ./
RUN go mod download
COPY whatsapp-bridge/ ./
RUN CGO_ENABLED=1 go build -o /out/whatsapp-bridge .

# ------------------------------------------------------------------
# Stage 2: final image
# ------------------------------------------------------------------
FROM ${BUILD_FROM}

# python3 runs the MCP server, ffmpeg converts audio to Opus/OGG for
# WhatsApp voice messages, uv installs the Python dependencies.
RUN \
    apk add --no-cache \
        python3 \
        py3-pip \
        ffmpeg \
    && pip install --no-cache-dir --break-system-packages uv

WORKDIR /app/whatsapp-mcp-server
COPY whatsapp-mcp-server/pyproject.toml whatsapp-mcp-server/uv.lock ./
RUN uv sync --frozen --no-dev
COPY whatsapp-mcp-server/*.py ./

COPY --from=bridge-builder /out/whatsapp-bridge /app/whatsapp-bridge/whatsapp-bridge

# Home Assistant App service definitions (s6-overlay)
COPY rootfs /

LABEL \
    org.opencontainers.image.title="WhatsApp MCP" \
    org.opencontainers.image.description="Model Context Protocol server for your personal WhatsApp account" \
    org.opencontainers.image.source="https://github.com/10bn/whatsapp-mcp-hass-addon" \
    org.opencontainers.image.licenses="MIT"
