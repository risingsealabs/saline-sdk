"""
RPC client for interacting with Saline nodes.

This module provides a unified client for submitting transactions and querying the Saline network.

IMPORTANT: Saline nodes and Tendermint RPC endpoints have specific behaviors:

1. Transaction Broadcasting:
   - broadcast_tx_commit and broadcast_tx_sync will return errors like
     "Failed decode: Error in $: not enough input" even for valid transactions if decoded incorrectly.
   - broadcast_tx_async is more permissive and will accept transactions, returning
     a transaction hash even if the transaction cannot be decoded.

2. Transaction Format:
   - Transactions must be properly serialized as JSON and base64 encoded.
   - POST requests with parameters in the body are more reliable than GET requests
     with URL parameters.

3. Error Handling:
   - Error responses often include hex-encoded error messages which need to be
     decoded for human readability.

Note on method naming conventions:
- Transaction broadcasting methods use descriptive names (tx_fire, tx_broadcast, tx_commit)
  that match the behavior rather than the RPC endpoint names
"""

import json
import logging
import binascii
import base64
from typing import Any, Dict, List, Optional, Tuple, Union
import aiohttp
import asyncio
import requests
from saline_sdk.rpc.error import RPCError
import saline_sdk.transaction.bindings as bindings
from saline_sdk.rpc.query_responses import (
    ParsedAllIntentsResponse,
    ParsedIntentInfo,
    ParsedWalletInfo,
    parse_dict_to_binding_intent
)

# Type for tokens
from enum import Enum

logger = logging.getLogger(__name__)

class Client:
    """
    Unified client for interacting with Saline nodes.

    Provides HTTP RPC connectivity to Saline nodes with functionality for:
    - Transaction broadcasting
    - Block and transaction querying
    - Balance querying
    - Intent querying and parsing
    - Wallet information retrieval
    - Aggregate balance queries

    Methods are provided in both asynchronous and synchronous versions:
    - Asynchronous methods (default) have no suffix
    - Synchronous wrappers have the _sync suffix

    Transaction broadcasting methods use descriptive names:
    - tx_fire: Fire-and-forget transaction (broadcast_tx_async RPC)
    - tx_broadcast: Submit and check transaction (broadcast_tx_sync RPC)
    - tx_commit: Submit and wait for block commit (broadcast_tx_commit RPC)
    """

    def __init__(
        self,
        http_url: str = "http://localhost:26657",
        debug: bool = False
    ):
        """
        Initialize the client.

        Args:
            http_url: Base URL for HTTP RPC endpoints
            debug: Enable debug logging
        """
        self.http_url = http_url
        self._request_id = 0
        self.debug = debug

    def _debug_log(self, message: str) -> None:
        """Log debug messages if debug mode is enabled."""
        if self.debug:
            logger.debug(message)
            print(f"DEBUG: {message}")

    def _get_request_id(self) -> int:
        """Get a unique request ID."""
        self._request_id += 1
        return self._request_id

    async def _make_request_async(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an asynchronous HTTP RPC request.

        Args:
            method: RPC method name
            params: Optional parameters

        Returns:
            Response data

        Raises:
            RPCError: If the request fails
        """
        headers = {"Content-Type": "application/json"}
        payload = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": method,
            "params": params or {}
        }

        try:
            self._debug_log(f"Making async HTTP request: {method} with params: {params}")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.http_url,
                    headers=headers,
                    json=payload
                ) as response:
                    response.raise_for_status()
                    result = await response.json()

                    if "error" in result:
                        error_msg = f"RPC error: {result['error']}"
                        self._debug_log(error_msg)
                        raise RPCError(error_msg)

                    return result["result"]

        except aiohttp.ClientError as e:
            error_msg = f"HTTP request failed: {str(e)}"
            self._debug_log(error_msg)
            raise RPCError(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"Failed to decode response: {str(e)}"
            self._debug_log(error_msg)
            raise RPCError(error_msg)

    def _hex_encode_data(self, data: str) -> str:
        """
        Convert data to hex-encoded string, ensuring even length.

        Args:
            data: String data to encode

        Returns:
            Hex-encoded string with even length
        """
        data_bytes = data.encode('utf-8')
        hex_data = binascii.hexlify(data_bytes).decode('ascii')

        # Ensure even length
        if len(hex_data) % 2 != 0:
            hex_data = '0' + hex_data

        return hex_data

    def _decode_response_value(self, value: str) -> Tuple[Optional[str], Optional[Any]]:
        """
        Decode a base64-encoded value from a response.

        Args:
            value: Base64-encoded string

        Returns:
            Tuple of (decoded_string, json_value or None)
        """
        try:
            decoded = base64.b64decode(value)
            decoded_str = decoded.decode('utf-8', errors='replace')

            try:
                json_value = json.loads(decoded_str)
                return decoded_str, json_value
            except json.JSONDecodeError:
                return decoded_str, None
        except Exception as e:
            self._debug_log(f"Error decoding: {e}")
            return None, None

    def _process_response(self, response_json: Dict[str, Any]) -> Tuple[int, Optional[str], Optional[Any]]:
        """
        Process a JSON-RPC response and extract the value.

        Args:
            response_json: Response JSON from the server

        Returns:
            Tuple of (code, decoded_value, json_value)
        """
        if "result" in response_json and "response" in response_json["result"]:
            response_data = response_json["result"]["response"]
            code = response_data.get("code", -1)

            if "value" in response_data and response_data["value"]:
                value = response_data["value"]
                decoded_str, json_value = self._decode_response_value(value)
                return code, decoded_str, json_value

        return -1, None, None

    # -------------------------------------------------------------------
    # Transaction broadcasting methods
    # -------------------------------------------------------------------

    async def tx_fire(self, tx_bytes: str) -> Dict[str, Any]:
        """
        Fire a transaction and return immediately (using broadcast_tx_async RPC).

        Fire and forget -  doesn't wait for any validation.

        Args:
            tx_bytes: Base64-encoded transaction bytes

        Returns:
            Transaction receipt with hash
        """
        return await self._make_request_async("broadcast_tx_async", {"tx": tx_bytes})

    async def tx_broadcast(self, tx_bytes: str) -> Dict[str, Any]:
        """
        Broadcast a transaction and wait for validation (using broadcast_tx_sync RPC).

         Submit and check -  waits for the transaction to be validated but not committed.

        Args:
            tx_bytes: Base64-encoded transaction bytes

        Returns:
            Transaction receipt with validation results
        """
        return await self._make_request_async("broadcast_tx_sync", {"tx": tx_bytes})

    async def tx_commit(self, tx_bytes: str) -> Dict[str, Any]:
        """
        Broadcast a transaction and wait for it to be committed (using broadcast_tx_commit RPC).

        Submit and wait -  waits for the transaction to be committed.

        Args:
            tx_bytes: Base64-encoded transaction bytes

        Returns:
            Transaction receipt with commit results
        """
        return await self._make_request_async("broadcast_tx_commit", {"tx": tx_bytes})

    # -------------------------------------------------------------------
    # Block and transaction methods
    # -------------------------------------------------------------------

    async def get_block(self, height: Optional[int] = None) -> Dict[str, Any]:
        """Get block at specified height or latest if not specified."""
        params = {}
        if height is not None:
            # Convert height to string as expected by Tendermint RPC for numeric params
            params["height"] = str(height)
        return await self._make_request_async("block", params)

    async def get_current_block(self) -> Dict[str, Any]:
        """Get the current block."""
        return await self.get_block()

    async def get_transactions(self, height: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get transactions from a block at specified height or latest if not specified."""
        block = await self.get_block(height)
        return block.get("block", {}).get("data", {}).get("txs", [])

    async def get_tx(self, tx_hash: str) -> Dict[str, Any]:
        """Get transaction by hash."""
        return await self._make_request_async("tx", {"hash": tx_hash})

    # -------------------------------------------------------------------
    # Query methods
    # -------------------------------------------------------------------

    # TODO: Replace UI encoding with JSON encoding
    async def get_status(self) -> Dict[str, Any]:
        """
        Get node status asynchronously.

        Returns:
            Node status information
        """
        return await self._make_request_async("status", {})

    async def abci_query_async(self, path: str, data: str, height: int = 0, prove: bool = False) -> Dict[str, Any]:
        """
        Make a direct ABCI query asynchronously.

        Args:
            path: Query path (e.g., "/store/balance", "/store/intent")
            data: Query data (hex-encoded)
            height: Block height (0 for latest)
            prove: Whether to include proofs

        Returns:
            Query result
        """
        params = {
            "path": path,
            "data": data,
            "height": str(height),
            "prove": prove
        }

        # Ensure data is properly quoted for the JSON-RPC API
        if not data.startswith('"') and '"' not in data:
            params["data"] = f'"{data}"'

        self._debug_log(f"ABCI query params: {params}")
        return await self._make_request_async("abci_query", params)

    async def get_balance_async(self, address: str, token: str = "USDC") -> Optional[float]:
        """
        Get the balance of a specific token for an address asynchronously.

        Args:
            address: Account address to query
            token: Token symbol (e.g., "USDC", "ETH")

        Returns:
            Balance amount or None if not found
        """
        self._debug_log(f"Querying balance for {address}, token: {token}")

        try:
            # Use wallet_info query instead of direct balance query
            wallet_info = await self.get_wallet_info_async(address)
            balances = wallet_info.get('balances', [])

            # Process the balances based on their format
            if isinstance(balances, dict):
                # If balances is a dictionary, just return the value for the token
                return float(balances.get(token, 0))

            # If balances is a list, search for the token
            for balance_item in balances:
                if isinstance(balance_item, list) and len(balance_item) >= 2:
                    bal_token, amount = balance_item[0], balance_item[1]
                    if bal_token == token:
                        return float(amount)
                elif isinstance(balance_item, dict):
                    bal_token = balance_item.get('token')
                    amount = balance_item.get('amount')
                    if bal_token == token and amount is not None:
                        return float(amount)

            # Token not found in balances
            return 0.0
        except Exception as e:
            self._debug_log(f"Error querying balance: {e}")
            return None

    async def get_all_balances_async(self, address: str) -> Dict[str, float]:
        """
        Get balances for all tokens for an address asynchronously.

        Args:
            address: Account address to query

        Returns:
            Dictionary mapping token symbols to balances
        """
        try:
            # Get all balances in one query using wallet_info
            wallet_info = await self.get_wallet_info_async(address)
            balances = wallet_info.get('balances', [])

            # Convert to a standard dictionary format
            balance_dict = {}

            # Process the balances based on their format
            if isinstance(balances, dict):
                # If it's already a dictionary, just convert values to float
                for token, amount in balances.items():
                    balance_dict[token] = float(amount)
            else:
                # If it's a list, process each balance item
                for balance_item in balances:
                    if isinstance(balance_item, list) and len(balance_item) >= 2:
                        token, amount = balance_item[0], balance_item[1]
                        balance_dict[token] = float(amount)
                    elif isinstance(balance_item, dict):
                        token = balance_item.get('token')
                        amount = balance_item.get('amount')
                        if token and amount is not None:
                            balance_dict[token] = float(amount)

            return balance_dict
        except Exception as e:
            self._debug_log(f"Error getting all balances: {e}")
            return {}

    async def get_wallet_info_async(self, address: str) -> ParsedWalletInfo:
        """
        Get wallet information for an address asynchronously.

        This method retrieves comprehensive information about a wallet, including:
        - All token balances
        - The wallet's intent (parsed into an SDK Intent object)

        Args:
            address: Address to get wallet info for

        Returns:
            ParsedWalletInfo dataclass containing parsed balances and intent.
        """
        self._debug_log(f"Querying wallet info for {address}")
        try:
            json_data = json.dumps(address)
            hex_data = self._hex_encode_data(json_data)

            url = f"{self.http_url}/abci_query"
            params = {
                "path": json.dumps("/store/wallet"),
                "data": f'"{hex_data}"',
                "height": "0",
                "prove": "false"
            }

            self._debug_log(f"Wallet info query params: {params}")

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    result = await response.json()

                    code, decoded_str, json_value = self._process_response(result)

                    if code != 0:
                        self._debug_log(f"Wallet info query returned error code {code}: {decoded_str}")
                        # Return a default WalletInfo on error, preserving raw data if available
                        return ParsedWalletInfo(address=address, balances={}, parsed_intent=None, raw_wallet_data=result.get('result'), error=f"RPC error code {code}: {decoded_str}")

                    # Process the returned JSON value
                    if json_value is None:
                        self._debug_log(f"Wallet info query returned None value.")
                        return ParsedWalletInfo(address=address, balances={}, parsed_intent=None, raw_wallet_data=json_value, error="RPC returned null value")

                    # --- Start Corrected Parsing Logic ---
                    balances_raw = None
                    raw_intent_data = None
                    balances_dict = {}
                    parsed_intent_obj: Optional[bindings.Intent] = None
                    parsing_error = None # Initialize parsing error

                    if isinstance(json_value, list) and len(json_value) >= 2:
                        balances_raw = json_value[0] # First element is expected to be balances
                        raw_intent_data = json_value[1] # Second element is expected to be intent
                        self._debug_log(f"Extracted balances_raw: {balances_raw}")
                        self._debug_log(f"Extracted raw_intent_data: {raw_intent_data}")

                        # Process balances (assuming balances_raw is a list of [token, amount])
                        if isinstance(balances_raw, list):
                            for item in balances_raw:
                                if isinstance(item, list) and len(item) == 2:
                                    token, amount_val = item # Amount might be float or int from RPC
                                    try:
                                        # Convert amount to int, handling potential floats from RPC
                                        balances_dict[token] = int(float(amount_val))
                                    except (ValueError, TypeError):
                                        self._debug_log(f"Could not parse amount for token {token}: {amount_val}")
                                else:
                                     self._debug_log(f"Unexpected balance item format: {item}")
                        else:
                            self._debug_log(f"Expected balances_raw to be a list, but got {type(balances_raw)}")
                            parsing_error = f"Invalid balance data format: {type(balances_raw)}"

                        # Process intent (raw_intent_data is expected to be a dict)
                        if raw_intent_data:
                            # --- Add Debug Logging for Raw Intent ---
                            self._debug_log(f"Raw intent data for {address}: {json.dumps(raw_intent_data)}")
                            # --- End Debug Logging ---
                            try:
                                # raw_intent_data should be a dict here for the parser
                                if isinstance(raw_intent_data, dict):
                                    parsed_intent_obj = parse_dict_to_binding_intent(raw_intent_data)
                                    if parsed_intent_obj is None:
                                        parsing_error = "Parsing intent returned None, structure likely invalid for bindings.py"
                                else:
                                    parsing_error = f"Expected raw_intent_data to be a dict, but got {type(raw_intent_data)}"
                            except Exception as e:
                                parsing_error = f"Intent parsing exception: {str(e)}"
                                self._debug_log(f"Intent parsing exception for wallet {address}: {parsing_error}")
                        else:
                             self._debug_log(f"No raw_intent_data found in response for {address}")


                    else:
                        self._debug_log(f"Unexpected json_value structure: {type(json_value)}. Expected list with >= 2 elements.")
                        parsing_error = "Invalid top-level data structure from RPC" # Set error if structure is wrong

                    # --- End Corrected Parsing Logic ---

                    return ParsedWalletInfo(
                        address=address,
                        balances=balances_dict,
                        parsed_intent=parsed_intent_obj,
                        raw_wallet_data=json_value,  # Store the whole original response for reference
                        error=parsing_error  # Store parsing error if any
                    )

        except Exception as e:
            self._debug_log(f"Error getting wallet info for {address}: {e}")
            # Return default WalletInfo on exception
            return ParsedWalletInfo(address=address, balances={}, parsed_intent=None, raw_wallet_data={"error": str(e)}, error=str(e))

    async def get_all_intents(self) -> ParsedAllIntentsResponse:
        """
        Get all intents in the system asynchronously.

        This method queries the node for all registered intents and parses them into
        specialized Intent objects from the SDK. It handles various intent types including
        All, Any, Restriction, Finite, Temporary and Signature intents.

        Returns:
            ParsedAllIntentsResponse object containing a dictionary of ParsedIntentInfo objects.
        """
        try:
            json_data = json.dumps([])  # For /store/intents, input is an empty array
            hex_data = self._hex_encode_data(json_data)

            params = {
                "path": json.dumps("/store/intents"),
                "data": f'"{hex_data}"',
                "height": "0",
                "prove": "false"
            }

            self._debug_log(f"All intents query params: {params}")

            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.http_url}/abci_query", params=params) as response:
                    response.raise_for_status()
                    result = await response.json()

                    code, decoded_str, json_value = self._process_response(result)

                    if code != 0 or json_value is None:
                        self._debug_log(f"Error querying all intents: {decoded_str}")
                        return ParsedAllIntentsResponse(intents={})  # Return empty response on error

            # --- END DEBUG PRINT ---

            intents_info: Dict[str, ParsedIntentInfo] = {}

            # Process the json_value which is expected to be a LIST
            # Each item in the list is another list: [raw_intent_data, addresses_data]
            if isinstance(json_value, list):
                for index, data_list in enumerate(json_value):
                    intent_id = f"intent_{index}" # Generate an ID based on index
                    raw_intent_data = None
                    addresses_data = []
                    parsed_intent_obj = None
                    error_msg = None

                    # Extract raw intent and addresses, handling potential structure variations
                    # data_list should be like [intent_dict, address_list_outer]
                    if isinstance(data_list, list) and len(data_list) >= 1:
                        raw_intent_data = data_list[0]  # Usually the first element
                        if len(data_list) >= 2:
                            addresses_data = data_list[1] # This is the list like [["addr_hash", []]]

                    # Attempt to parse the raw intent data using the bindings parser
                    if raw_intent_data:  # Pass the raw data which might be list or dict
                        try:
                            parsed_intent_obj = parse_dict_to_binding_intent(raw_intent_data)
                            if parsed_intent_obj is None:
                                error_msg = "Parsing returned None (structure invalid for bindings.py?)"
                        except Exception as e:
                            error_msg = f"Parsing exception: {str(e)}"
                            self._debug_log(f"Parsing exception for {intent_id}: {error_msg}")

                    # Add error if data_list structure was wrong
                    elif not error_msg:
                        error_msg = f"Unexpected structure for data_list item {index}: {type(data_list)}"

                    intents_info[intent_id] = ParsedIntentInfo(
                        intent_id=intent_id,
                        parsed_intent=parsed_intent_obj,
                        raw_intent_data=raw_intent_data,
                        addresses=addresses_data,
                        error=error_msg
                    )
            else:
                self._debug_log(f"Unexpected top-level structure for all intents response: {type(json_value)}")

            return ParsedAllIntentsResponse(intents=intents_info)

        except Exception as e:
            self._debug_log(f"Error getting all intents: {e}")
            return ParsedAllIntentsResponse(intents={})  # Return empty response on exception
