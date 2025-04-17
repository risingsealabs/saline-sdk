import asyncio
from typing import Dict, List, Optional, Union
from saline_sdk.rpc.client import Client
import saline_sdk.transaction.bindings as bindings
from saline_sdk.rpc.query_responses import (
    ParsedWalletInfo,
    ParsedAllIntentsResponse,
    ParsedIntentInfo,
    contains_binding_type
)

RPC_URL = "https://node0.try-saline.com"

# --- Simplified Swap Check (using imported helper) ---

def is_likely_swap(intent: Optional[bindings.Intent]) -> bool:
    """Check if an intent matches a simple swap heuristic (All containing Send and Receive)."""
    if not isinstance(intent, bindings.All):
        return False # Heuristic: Top level must be All

    # Check if Send and Receive expressions exist anywhere within the 'All' structure
    has_send = contains_binding_type(intent, bindings.Send)
    has_receive = contains_binding_type(intent, bindings.Receive)

    return has_send and has_receive

# --- End Helper functions ---

def print_intent_structure(intent: Optional[Union[bindings.Intent, bindings.Expr]], indent: int = 0) -> None:
    """Print the structure of an Intent or Expr from bindings.py."""
    if intent is None:
        print(f"{' ' * indent}None")
        return

    # Get class name for the tag/type
    intent_name = intent.__class__.__name__
    print(f"{' ' * indent}{intent_name}", end="")

    # Print specific attributes based on the class from bindings.py
    if isinstance(intent, bindings.Counterparty):
        print(f" (address={intent.address})")
    elif isinstance(intent, bindings.Signature):
        print(f" (signer={intent.signer})")
    elif isinstance(intent, bindings.Lit):
        print(f" (value={intent.value!r})")
    elif isinstance(intent, (bindings.Receive, bindings.Send, bindings.Balance)):
        print(f" (token={intent.token.name})") # Access enum name
    else:
        print() # Newline for non-leaf nodes

    # Handle recursive printing for composite types
    if isinstance(intent, (bindings.All, bindings.Any)):
        for i, child in enumerate(intent.children):
            print(f"{' ' * (indent+2)}Child {i+1}:")
            print_intent_structure(child, indent + 4)
        if isinstance(intent, bindings.Any):
            print(f"{' ' * (indent+2)}Threshold: {intent.threshold}")
    elif isinstance(intent, bindings.Restriction):
        print(f"{'  ' * indent}LHS:")
        print_intent_structure(intent.lhs, indent + 1) # lhs is an Expr
        print(f"{'  ' * indent}RHS:")
        print_intent_structure(intent.rhs, indent + 1) # rhs is an Expr
        print(f"{'  ' * indent}Relation: {intent.relation.name}") # Access enum name
    elif isinstance(intent, (bindings.Finite, bindings.Temporary)):
        print(f"{'  ' * indent}Inner:")
        print_intent_structure(intent.inner, indent + 1)
        if isinstance(intent, bindings.Finite):
            print(f"{'  ' * indent}Uses: {intent.uses}")
        elif isinstance(intent, bindings.Temporary):
            print(f"{'  ' * indent}Duration: {intent.duration}")
            print(f"{'  ' * indent}AvailableAfter: {intent.availableAfter}")
    elif isinstance(intent, bindings.Arithmetic2):
        print(f"{'  ' * indent}LHS:")
        print_intent_structure(intent.lhs, indent + 1)
        print(f"{'  ' * indent}RHS:")
        print_intent_structure(intent.rhs, indent + 1)
        print(f"{'  ' * indent}Operation: {intent.operation.name}")
    # Other types (like Var) could be added if needed for printing

async def main():
    client = Client(debug=True,http_url=RPC_URL)

    all_intents_response: ParsedAllIntentsResponse = await client.get_all_intents()
    print(f"\n========== Query All Intents Results ==========")
    print(f"Found {len(all_intents_response.intents)} raw intent entries")

    intent_types = {}
    parsing_errors = 0
    likely_swaps = 0
    for intent_info in all_intents_response.intents.values():
        if intent_info.error:
            # Print error more prominently if parsing failed
            if intent_info.parsed_intent is None:
                print(f"!!! Parsing FAILED for intent {intent_info.intent_id}: {intent_info.error}")
                parsing_errors += 1
            else: # Log less critical errors if parsing somehow succeeded despite error
                print(f"Note processing intent {intent_info.intent_id}: {intent_info.error}")
        if intent_info.parsed_intent:
            intent_type = intent_info.parsed_intent.__class__.__name__ # Use class name from bindings
            intent_types[intent_type] = intent_types.get(intent_type, 0) + 1
            if is_likely_swap(intent_info.parsed_intent):
                likely_swaps += 1

    print(f"Successfully parsed {len(intent_types)} intent types.")
    if parsing_errors > 0:
        print(f"Failed to parse {parsing_errors} intent entries.")

    if likely_swaps > 0:
        print(f"Found {likely_swaps} entries matching the simple swap heuristic.")

    if intent_types: # Only print summary if some were parsed
        print("\nParsed Intent Type Summary:")
        for intent_type, count in intent_types.items():
            print(f"  {intent_type}: {count}")

if __name__ == "__main__":
    asyncio.run(main())
