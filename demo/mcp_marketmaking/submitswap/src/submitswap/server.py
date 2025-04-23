import asyncio
import json
from typing import Dict

from saline_sdk.account import Account
from saline_sdk.rpc.client import Client
from saline_sdk.transaction.bindings import (
    NonEmpty, Transaction, TransferFunds, Token
)
from saline_sdk.transaction.tx import prepareSimpleTx, print_tx_errors

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio

server = Server("submitswap")

# Config
RPC_URL = "https://node0.try-saline.com"
TEST_MNEMONIC = "frequent crazy crack front play age luggage bomb buddy uncle tobacco steak"
AGENT_ROOT = Account.from_mnemonic(TEST_MNEMONIC)
AGENT_SIGNER = AGENT_ROOT.create_subaccount(label="agent-signer")

# @server.list_resources()
# async def handle_list_resources() -> list[types.Resource]:
#     """
#     List available note resources.
#     Each note is exposed as a resource with a custom note:// URI scheme.
#     """
#     return [
#         types.Resource(
#             uri=AnyUrl(f"note://internal/{name}"),
#             name=f"Note: {name}",
#             description=f"A simple note named {name}",
#             mimeType="text/plain",
#         )
#         for name in notes
#     ]

# @server.read_resource()
# async def handle_read_resource(uri: AnyUrl) -> str:
#     """
#     Read a specific note's content by its URI.
#     The note name is extracted from the URI host component.
#     """
#     if uri.scheme != "note":
#         raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

#     name = uri.path
#     if name is not None:
#         name = name.lstrip("/")
#         return notes[name]
#     raise ValueError(f"Note not found: {name}")

@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """
    List available prompts.
    Each prompt can have optional arguments to customize its behavior.
    """
    return [
        types.Prompt(
            name="summarize-notes",
            description="Creates a summary of all notes",
            arguments=[
                types.PromptArgument(
                    name="style",
                    description="Style of the summary (brief/detailed)",
                    required=False,
                )
            ],
        )
    ]

# @server.get_prompt()
# async def handle_get_prompt(
#     name: str, arguments: dict[str, str] | None
# ) -> types.GetPromptResult:
#     """
#     Generate a prompt by combining arguments with server state.
#     The prompt includes all current notes and can be customized via arguments.
#     """
#     if name != "summarize-notes":
#         raise ValueError(f"Unknown prompt: {name}")

#     style = (arguments or {}).get("style", "brief")
#     detail_prompt = " Give extensive details." if style == "detailed" else ""

#     return types.GetPromptResult(
#         description="Summarize the current notes",
#         messages=[
#             types.PromptMessage(
#                 role="user",
#                 content=types.TextContent(
#                     type="text",
#                     text=f"Here are the current notes to summarize:{detail_prompt}\n\n"
#                     + "\n".join(
#                         f"- {name}: {content}"
#                         for name, content in notes.items()
#                     ),
#                 ),
#             )
#         ],
#     )

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="execute-swap",
            description="Execute a matched swap transaction between two addresses.",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_address": {"type": "string"},
                    "to_address": {"type": "string"},
                    "give_token": {"type": "string"},
                    "give_amount": {"type": "integer"},
                    "receive_token": {"type": "string"},
                    "receive_amount": {"type": "integer"},
                },
                "required": ["from_address", "to_address", "give_token", "give_amount", "receive_token", "receive_amount"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    if name != "execute-swap":
        raise ValueError(f"Unknown tool: {name}")

    if not arguments:
        raise ValueError("Missing arguments")

    from_address = arguments["from_address"].removeprefix("nacl:")
    to_address = arguments["to_address"].removeprefix("nacl:")
    give_token = arguments["give_token"]
    give_amount = arguments["give_amount"]
    receive_token = arguments["receive_token"]
    receive_amount = arguments["receive_amount"]

    # Load matcher signing account
    # root_account = Account.from_mnemonic(TEST_MNEMONIC)
    # matcher_account = root_account.create_subaccount(label="matcher")
    client = Client(http_url=RPC_URL)

    try:
        # Construct transfer instructions
        instruction1 = TransferFunds(source=from_address, target=to_address, funds={give_token: give_amount})
        instruction2 = TransferFunds(source=to_address, target=from_address, funds={receive_token: receive_amount})

        tx = Transaction(instructions=NonEmpty.from_list([instruction1, instruction2]))
        signed_tx = prepareSimpleTx(AGENT_SIGNER, tx)

        result = await client.tx_commit(signed_tx)
        error_output = print_tx_errors(result)

        output_text = f"Transaction result:\n{json.dumps(result, indent=2)}"
        if error_output:
            output_text += f"\n\nError Details:\n{error_output}"

        return [
            types.TextContent(
                type="text",
                text=output_text
            )
        ]
    except Exception as e:
        return [types.TextContent(type="text", text=f"🚨 Exception during transaction: {str(e)}")]

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="submitswap",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )