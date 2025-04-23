import asyncio

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio
import json
from saline_sdk.account import Account
from saline_sdk.rpc.client import Client
from saline_sdk.transaction.bindings import NonEmpty, Transaction, TransferFunds
from saline_sdk.transaction.tx import prepareSimpleTx, print_tx_errors

# Store notes as a simple key-value dict to demonstrate state management
notes: dict[str, str] = {}

server = Server("salinetx")

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """
    List available Saline resources (e.g. last transaction).
    """
    return [
        types.Resource(
            uri=AnyUrl(f"tx://internal/{name}"),
            name=f"Transaction: {name}",
            description=f"Result from Saline transaction `{name}`",
            mimeType="application/json",
        )
        for name in notes
    ]


@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """
    Read a specific Saline resource (e.g. tx) by its URI.
    The resource key is extracted from the URI path.
    """
    if uri.scheme not in {"tx", "saline"}:
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    key = uri.path.lstrip("/")
    if key in notes:
        return notes[key]
    raise ValueError(f"Resource not found: {key}")

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

@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """
    Generate a summary of the latest Saline transaction result.
    """
    if name != "summarize-transaction":
        raise ValueError(f"Unknown prompt: {name}")

    tx_output = notes.get("last_tx", "No transaction has been submitted yet.")

    return types.GetPromptResult(
        description="Summarize the latest Saline transaction",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Here's the latest transaction result:\n\n{tx_output}",
                ),
            )
        ],
    )

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="submit-saline-transfer",
            description="Submit a transaction on Saline Network",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_wallet": {"type": "string", "description": "Sender wallet address or 'my wallet'"},
                    "to_wallet": {"type": "string", "description": "Recipient wallet address or 'my wallet'"},
                    "token": {"type": "string", "description": "Token symbol (e.g. ETH, BTC, USDC)"},
                    "amount": {"type": "number", "description": "Amount to transfer"},
                },
                "required": ["from_wallet", "to_wallet", "token", "amount"],
            },
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    if name != "submit-saline-transfer":
        raise ValueError(f"Unknown tool: {name}")
    if not arguments:
        raise ValueError("Missing arguments")

    from_wallet = arguments.get("from_wallet")
    to_wallet = arguments.get("to_wallet")
    token = arguments.get("token")
    amount = arguments.get("amount")

    try:
        result = await submit_saline_tx(from_wallet, to_wallet, token, amount)
        return [types.TextContent(type="text", text=f"Transaction submitted:\n{json.dumps(result, indent=2)}")]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Transaction failed: {str(e)}")]


async def submit_saline_tx(from_wallet: str, to_wallet: str, token: str, amount: float) -> dict:
   


    RPC_URL = "https://node1.try-saline.com"
    AGENT_MNEMONIC = "morning liberty powder mammal divert snake rug snap supply erosion museum search"
    # public_address = nacl:0xab51cd13d99ad704f1f47744d5d35febb1d1d73f6c7e8da4aa7092a1955f438dfd1dec98bde22393806db9a2b063a0ba
    agent_root = Account.from_mnemonic(AGENT_MNEMONIC)
    agent_wallet = agent_root.create_subaccount(label="Agent_address")

    def clean_address(addr: str) -> str:
        return addr.removeprefix("nacl:0x").lower()

    sender_pub = clean_address(from_wallet)
    receiver_pub = clean_address(to_wallet)

    transfer = TransferFunds(
        source=sender_pub,
        target=receiver_pub,
        funds={token.upper(): amount},
    )

    tx = Transaction(
        instructions=NonEmpty.from_list([transfer]),
    )


    rpc = Client(http_url=RPC_URL)
    print("Submitting transfer to rule address...")
    try:
        signed_tx = prepareSimpleTx(agent_wallet, tx)
        result = await rpc.tx_commit(signed_tx)
        print_tx_errors(result)
        print("\n✅ Transaction submitted successfully:")
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        raise RuntimeError(f"Unhandled exception during tx: {e}")


async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="salinetx",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )