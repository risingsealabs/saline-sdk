import asyncio
from typing import Dict, List
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio
from saline_sdk.rpc.client import Client
from saline_sdk.rpc.query_responses import (
    ParsedAllIntentsResponse, ParsedIntentInfo, contains_binding_type
)
import saline_sdk.transaction.bindings as bindings

# Store notes as a simple key-value dict to demonstrate state management
notes: dict[str, str] = {}

# --- MCP Server Init ---
server = Server("queryswap")

# --- In-memory storage for swap intents ---
swaps: Dict[str, str] = {}

RPC_URL = "https://node0.try-saline.com"

# --- Swap Analysis Utilities ---
def is_likely_swap(intent: bindings.Intent) -> bool:
    return (
        isinstance(intent, bindings.All)
        and contains_binding_type(intent, bindings.Send)
        and contains_binding_type(intent, bindings.Receive)
    )

def extract_swap_details(intent_info: ParsedIntentInfo) -> str:
    parsed = intent_info.parsed_intent
    if not is_likely_swap(parsed):
        return ""

    send_token = receive_token = None
    send_amount = receive_amount = None

    def extract_from_restriction(restriction: bindings.Restriction):
        nonlocal send_token, send_amount, receive_token, receive_amount
        if isinstance(restriction.rhs, bindings.Lit):
            if isinstance(restriction.lhs, bindings.Send):
                send_token = restriction.lhs.token.name
                send_amount = restriction.rhs.value
            elif isinstance(restriction.lhs, bindings.Receive):
                receive_token = restriction.lhs.token.name
                receive_amount = restriction.rhs.value

    if isinstance(parsed, bindings.All):
        for child in parsed.children:
            if isinstance(child, bindings.Restriction):
                extract_from_restriction(child)

    try:
        address = intent_info.addresses[0][0]
    except Exception:
        address = "unknown"

    if all([send_token, send_amount, receive_token, receive_amount]):
        return f"{address}: {send_amount} {send_token} -> {receive_amount} {receive_token}"
    return ""

async def update_swap_data():
    client = Client(http_url=RPC_URL)
    all_intents_response: ParsedAllIntentsResponse = await client.get_all_intents()

    swaps.clear()
    for intent_info in all_intents_response.intents.values():
        if intent_info.error or not intent_info.parsed_intent:
            continue
        swap = extract_swap_details(intent_info)
        if swap:
            swaps[intent_info.intent_id] = swap

@server.list_resources()
async def handle_list_resources() -> List[types.Resource]:
    await update_swap_data()
    return [
        types.Resource(
            uri=AnyUrl(f"swap://internal/{intent_id}"),
            name=f"Swap Intent {intent_id[:6]}...",
            description=summary,
            mimeType="text/plain",
        )
        for intent_id, summary in swaps.items()
    ]

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    if uri.scheme != "swap":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")
    key = uri.path.lstrip("/")
    return swaps.get(key, f"Swap intent {key} not found.")

@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    return [
        types.Prompt(
            name="list-swap-intents",
            description="Show a list of all on-chain swap intents",
            arguments=[],
        )
    ]


@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    if name != "list-swap-intents":
        raise ValueError(f"Unknown prompt: {name}")
    
    await update_swap_data()
    return types.GetPromptResult(
        description="List of swap intents currently on chain",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text="\n".join(
                        f"- {swap}" for swap in swaps.values()
                    ) or "No swap intents found."
                ),
            )
        ],
    )


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="find-matching-swaps",
            description="Fetch the list of swap intents from the Saline Network so the assistant can analyze and match them.",
            inputSchema={"type": "object", "properties": {}},
        )
    ]



@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    if name != "find-matching-swaps":
        raise ValueError(f"Unknown tool: {name}")

    await update_swap_data()

    if not swaps:
        return [
            types.TextContent(type="text", text="No swap intents found on-chain.")
        ]

    return [
        types.TextContent(
            type="text",
            text="Here is the current list of swap intents from the Saline Network:\n\n" +
                 "\n".join(f"- {intent}" for intent in swaps.values())
        )
    ]



async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="queryswap",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )