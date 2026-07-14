import os
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from whatsapp import (
    search_contacts as whatsapp_search_contacts,
    list_messages as whatsapp_list_messages,
    list_chats as whatsapp_list_chats,
    get_chat as whatsapp_get_chat,
    get_direct_chat_by_contact as whatsapp_get_direct_chat_by_contact,
    get_contact_chats as whatsapp_get_contact_chats,
    get_last_interaction as whatsapp_get_last_interaction,
    get_message_context as whatsapp_get_message_context,
    send_message as whatsapp_send_message,
    send_file as whatsapp_send_file,
    send_audio_message as whatsapp_audio_voice_message,
    download_media as whatsapp_download_media,
    list_newsletters as whatsapp_list_newsletters,
    unfollow_newsletter as whatsapp_unfollow_newsletter,
)

# Initialize FastMCP server
mcp = FastMCP(
    "whatsapp",
    host=os.environ.get("MCP_HOST", "0.0.0.0"),
    port=int(os.environ.get("MCP_PORT", "8081")),
)


def _jsonable(value: Any) -> Any:
    """Recursively convert dataclasses (Chat, Contact, Message, MessageContext,
    ...) and datetimes into the plain dicts/strings the declared tool output
    schemas promise. Without this, FastMCP's output validation rejects a
    dataclass instance where a dict is expected.
    """
    if is_dataclass(value) and not isinstance(value, type):
        return {k: _jsonable(v) for k, v in asdict(value).items()}
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    return value


def _chat_to_dict(chat) -> Dict[str, Any]:
    d = _jsonable(chat)
    d["is_group"] = chat.is_group
    return d


@mcp.tool()
def search_contacts(query: str) -> List[Dict[str, Any]]:
    """Search WhatsApp contacts by name or phone number.

    Args:
        query: Search term to match against contact names or phone numbers
    """
    contacts = whatsapp_search_contacts(query)
    return [_jsonable(c) for c in contacts]

@mcp.tool()
def list_messages(
    after: Optional[str] = None,
    before: Optional[str] = None,
    sender_phone_number: Optional[str] = None,
    chat_jid: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_context: bool = True,
    context_before: int = 1,
    context_after: int = 1
) -> List[Dict[str, Any]]:
    """Get WhatsApp messages matching specified criteria with optional context.
    
    Args:
        after: Optional ISO-8601 formatted string to only return messages after this date
        before: Optional ISO-8601 formatted string to only return messages before this date
        sender_phone_number: Optional phone number to filter messages by sender
        chat_jid: Optional chat JID to filter messages by chat
        query: Optional search term to filter messages by content
        limit: Maximum number of messages to return (default 20)
        page: Page number for pagination (default 0)
        include_context: Whether to include messages before and after matches (default True)
        context_before: Number of messages to include before each match (default 1)
        context_after: Number of messages to include after each match (default 1)
    """
    messages = whatsapp_list_messages(
        after=after,
        before=before,
        sender_phone_number=sender_phone_number,
        chat_jid=chat_jid,
        query=query,
        limit=limit,
        page=page,
        include_context=include_context,
        context_before=context_before,
        context_after=context_after
    )
    return [_jsonable(m) for m in messages]

@mcp.tool()
def list_chats(
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_last_message: bool = True,
    sort_by: str = "last_active"
) -> List[Dict[str, Any]]:
    """Get WhatsApp chats matching specified criteria.
    
    Args:
        query: Optional search term to filter chats by name or JID
        limit: Maximum number of chats to return (default 20)
        page: Page number for pagination (default 0)
        include_last_message: Whether to include the last message in each chat (default True)
        sort_by: Field to sort results by, either "last_active" or "name" (default "last_active")
    """
    chats = whatsapp_list_chats(
        query=query,
        limit=limit,
        page=page,
        include_last_message=include_last_message,
        sort_by=sort_by
    )
    return [_chat_to_dict(c) for c in chats]

@mcp.tool()
def get_chat(chat_jid: str, include_last_message: bool = True) -> Optional[Dict[str, Any]]:
    """Get WhatsApp chat metadata by JID.

    Args:
        chat_jid: The JID of the chat to retrieve
        include_last_message: Whether to include the last message (default True)
    """
    chat = whatsapp_get_chat(chat_jid, include_last_message)
    return _chat_to_dict(chat) if chat else None

@mcp.tool()
def get_direct_chat_by_contact(sender_phone_number: str) -> Optional[Dict[str, Any]]:
    """Get WhatsApp chat metadata by sender phone number.

    Args:
        sender_phone_number: The phone number to search for
    """
    chat = whatsapp_get_direct_chat_by_contact(sender_phone_number)
    return _chat_to_dict(chat) if chat else None

@mcp.tool()
def get_contact_chats(jid: str, limit: int = 20, page: int = 0) -> List[Dict[str, Any]]:
    """Get all WhatsApp chats involving the contact.

    Args:
        jid: The contact's JID to search for
        limit: Maximum number of chats to return (default 20)
        page: Page number for pagination (default 0)
    """
    chats = whatsapp_get_contact_chats(jid, limit, page)
    return [_chat_to_dict(c) for c in chats]

@mcp.tool()
def get_last_interaction(jid: str) -> str:
    """Get most recent WhatsApp message involving the contact.
    
    Args:
        jid: The JID of the contact to search for
    """
    message = whatsapp_get_last_interaction(jid)
    return message

@mcp.tool()
def get_message_context(
    message_id: str,
    before: int = 5,
    after: int = 5
) -> Dict[str, Any]:
    """Get context around a specific WhatsApp message.
    
    Args:
        message_id: The ID of the message to get context for
        before: Number of messages to include before the target message (default 5)
        after: Number of messages to include after the target message (default 5)
    """
    context = whatsapp_get_message_context(message_id, before, after)
    return _jsonable(context)

@mcp.tool()
def send_message(
    recipient: str,
    message: str
) -> Dict[str, Any]:
    """Send a WhatsApp message to a person or group. For group chats use the JID.

    Args:
        recipient: The recipient - either a phone number with country code but no + or other symbols,
                 or a JID (e.g., "123456789@s.whatsapp.net" or a group JID like "123456789@g.us")
        message: The message text to send
    
    Returns:
        A dictionary containing success status and a status message
    """
    # Validate input
    if not recipient:
        return {
            "success": False,
            "message": "Recipient must be provided"
        }
    
    # Call the whatsapp_send_message function with the unified recipient parameter
    success, status_message = whatsapp_send_message(recipient, message)
    return {
        "success": success,
        "message": status_message
    }

@mcp.tool()
def send_file(recipient: str, media_path: str) -> Dict[str, Any]:
    """Send a file such as a picture, raw audio, video or document via WhatsApp to the specified recipient. For group messages use the JID.
    
    Args:
        recipient: The recipient - either a phone number with country code but no + or other symbols,
                 or a JID (e.g., "123456789@s.whatsapp.net" or a group JID like "123456789@g.us")
        media_path: The absolute path to the media file to send (image, video, document)
    
    Returns:
        A dictionary containing success status and a status message
    """
    
    # Call the whatsapp_send_file function
    success, status_message = whatsapp_send_file(recipient, media_path)
    return {
        "success": success,
        "message": status_message
    }

@mcp.tool()
def send_audio_message(recipient: str, media_path: str) -> Dict[str, Any]:
    """Send any audio file as a WhatsApp audio message to the specified recipient. For group messages use the JID. If it errors due to ffmpeg not being installed, use send_file instead.
    
    Args:
        recipient: The recipient - either a phone number with country code but no + or other symbols,
                 or a JID (e.g., "123456789@s.whatsapp.net" or a group JID like "123456789@g.us")
        media_path: The absolute path to the audio file to send (will be converted to Opus .ogg if it's not a .ogg file)
    
    Returns:
        A dictionary containing success status and a status message
    """
    success, status_message = whatsapp_audio_voice_message(recipient, media_path)
    return {
        "success": success,
        "message": status_message
    }

@mcp.tool()
def download_media(message_id: str, chat_jid: str) -> Dict[str, Any]:
    """Download media from a WhatsApp message and get the local file path.
    
    Args:
        message_id: The ID of the message containing the media
        chat_jid: The JID of the chat containing the message
    
    Returns:
        A dictionary containing success status, a status message, and the file path if successful
    """
    file_path = whatsapp_download_media(message_id, chat_jid)
    
    if file_path:
        return {
            "success": True,
            "message": "Media downloaded successfully",
            "file_path": file_path
        }
    else:
        return {
            "success": False,
            "message": "Failed to download media"
        }

@mcp.tool()
def list_newsletters() -> List[Dict[str, Any]]:
    """List the WhatsApp channels/newsletters this account is subscribed to.

    Returns:
        A list of newsletters, each with jid, name and subscriber_count. Pass
        a jid to unfollow_newsletter to unsubscribe from it.
    """
    return whatsapp_list_newsletters()

@mcp.tool()
def unfollow_newsletter(channel_jid: str) -> Dict[str, Any]:
    """Unfollow (unsubscribe from) a WhatsApp channel/newsletter. Use list_newsletters first to find the jid.

    Args:
        channel_jid: The JID of the channel/newsletter to unfollow (from list_newsletters)

    Returns:
        A dictionary containing success status and a status message
    """
    success, status_message = whatsapp_unfollow_newsletter(channel_jid)
    return {
        "success": success,
        "message": status_message
    }

def _run_streamable_http() -> None:
    """Run the server over streamable-http, gated by a shared secret.

    A stdio MCP server is only reachable by a process that spawns it
    locally. Once exposed over the network (e.g. as a Home Assistant app
    service) it becomes reachable by anything on the LAN unless we require a
    secret. The secret itself is resolved and persisted by the app's run
    script (see rootfs/etc/services.d/), not here - this just enforces it.

    Two equivalent ways to authenticate:
      - POST/GET/DELETE /mcp                with header Authorization: Bearer <secret>
      - POST/GET/DELETE /private_<secret>    no header needed, the URL itself
        is the credential (same idea as Home Assistant's own
        /api/webhook/<id> URLs) - for MCP clients that only accept a bare
        URL and can't set custom headers.
    An invalid /private_<token> gets a plain 404, not a 401, so it doesn't
    even reveal that the path is meaningful.
    """
    import hmac
    import uvicorn
    from starlette.responses import JSONResponse

    auth_token = os.environ.get("MCP_AUTH_TOKEN", "").strip()
    mcp_path = mcp.settings.streamable_http_path
    inner_app = mcp.streamable_http_app()

    def valid(candidate: str, expected: str) -> bool:
        return hmac.compare_digest(candidate.encode(), expected.encode())

    if not auth_token:
        print(
            "WARNING: no MCP auth secret is configured. The WhatsApp MCP "
            "server is reachable by anyone who can reach this port on the "
            "network, without authentication.",
            flush=True,
        )
        app = inner_app
    else:
        async def app(scope, receive, send):
            if scope["type"] != "http":
                await inner_app(scope, receive, send)
                return

            path = scope["path"]
            if path.startswith("/private_"):
                candidate = path[len("/private_"):]
                if not valid(candidate, auth_token):
                    response = JSONResponse({"error": "Not Found"}, status_code=404)
                    await response(scope, receive, send)
                    return
                scope = {**scope, "path": mcp_path, "raw_path": mcp_path.encode()}
            elif path == mcp_path:
                headers = dict(scope.get("headers") or [])
                provided = headers.get(b"authorization", b"").decode()
                if not valid(provided, f"Bearer {auth_token}"):
                    response = JSONResponse({"error": "Unauthorized"}, status_code=401)
                    await response(scope, receive, send)
                    return

            await inner_app(scope, receive, send)

        public_port = os.environ.get("MCP_PUBLIC_PORT", str(mcp.settings.port))
        print(f"No-header MCP URL: http://<home-assistant-host>:{public_port}/private_{auth_token}", flush=True)
        print(
            "Replace <home-assistant-host> with the same host/IP you use for "
            "Home Assistant itself.",
            flush=True,
        )

    uvicorn.run(app, host=mcp.settings.host, port=mcp.settings.port)


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio").strip().lower()
    if transport == "streamable-http":
        _run_streamable_http()
    else:
        mcp.run(transport="stdio")