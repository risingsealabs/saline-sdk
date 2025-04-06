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
from typing import Any, Dict, List, Optional, Tuple
import aiohttp
import asyncio
import requests
from saline_sdk.rpc.error import RPCError
from saline_sdk.transaction.bindings import Intent, All, Any, Finite, Temporary, Signature, Lit, Restriction, Relation, Token

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

    def _make_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a synchronous HTTP RPC request.

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
            self._debug_log(f"Making sync HTTP request: {method} with params: {params}")
            response = requests.post(
                self.http_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            if "error" in result:
                error_msg = f"RPC error: {result['error']}"
                self._debug_log(error_msg)
                raise RPCError(error_msg)

            return result["result"]

        except requests.RequestException as e:
            error_msg = f"HTTP request failed: {str(e)}"
            self._debug_log(error_msg)
            raise RPCError(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"Failed to decode response: {str(e)}"
            self._debug_log(error_msg)
            raise RPCError(error_msg)

    def _run_async(self, coro):
        """Run a coroutine in a new event loop."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

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

    def tx_fire_sync(self, tx_bytes: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for tx_fire.

        Args:
            tx_bytes: Base64-encoded transaction bytes

        Returns:
            Transaction receipt with hash
        """
        return self._run_async(self.tx_fire(tx_bytes))

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

    def tx_broadcast_sync(self, tx_bytes: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for tx_broadcast.

        Args:
            tx_bytes: Base64-encoded transaction bytes

        Returns:
            Transaction receipt with validation results
        """
        return self._run_async(self.tx_broadcast(tx_bytes))

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

    def tx_commit_sync(self, tx_bytes: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for tx_commit.

        Args:
            tx_bytes: Base64-encoded transaction bytes

        Returns:
            Transaction receipt with commit results
        """
        return self._run_async(self.tx_commit(tx_bytes))

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

    def get_block_sync(self, height: Optional[int] = None) -> Dict[str, Any]:
        """Synchronous wrapper for get_block."""
        return self._run_async(self.get_block(height))

    async def get_current_block(self) -> Dict[str, Any]:
        """Get the current block."""
        return await self.get_block()

    def get_current_block_sync(self) -> Dict[str, Any]:
        """Synchronous wrapper for get_current_block."""
        return self._run_async(self.get_current_block())

    async def get_transactions(self, height: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get transactions from a block at specified height or latest if not specified."""
        block = await self.get_block(height)
        return block.get("block", {}).get("data", {}).get("txs", [])

    def get_transactions_sync(self, height: Optional[int] = None) -> List[Dict[str, Any]]:
        """Synchronous wrapper for get_transactions."""
        return self._run_async(self.get_transactions(height))

    async def get_tx(self, tx_hash: str) -> Dict[str, Any]:
        """Get transaction by hash."""
        return await self._make_request_async("tx", {"hash": tx_hash})

    def get_tx_sync(self, tx_hash: str) -> Dict[str, Any]:
        """Synchronous wrapper for get_tx."""
        return self._run_async(self.get_tx(tx_hash))


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

    def get_status(self) -> Dict[str, Any]:
        """
        Get node status synchronously.

        Returns:
            Node status information
        """
        return self._make_request("status", {})

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

    def abci_query(self, path: str, data: str, height: int = 0, prove: bool = False) -> Dict[str, Any]:
        """
        Make a direct ABCI query synchronously.

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
        return self._make_request("abci_query", params)

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

    def get_balance(self, address: str, token: str = "USDC") -> Optional[float]:
        """
        Get the balance of a specific token for an address synchronously.

        Args:
            address: Account address to query
            token: Token symbol (e.g., "USDC", "ETH")

        Returns:
            Balance amount or None if not found
        """
        return self._run_async(self.get_balance_async(address, token))

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

    def get_all_balances(self, address: str) -> Dict[str, float]:
        """
        Get all token balances for an address.

        Args:
            address: Address to query balances for

        Returns:
            Dictionary mapping token symbols to amounts
        """
        return self._run_async(self.get_all_balances_async(address))

    async def get_intent_async(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Get the intent for an address asynchronously.

        Args:
            address: Account address to query

        Returns:
            Intent data or None if not found
        """
        self._debug_log(f"Querying intent for {address}")

        try:
            json_data = json.dumps(address)
            hex_data = self._hex_encode_data(json_data)

            url = f"{self.http_url}/abci_query"
            params = {
                "path": json.dumps("/store/intent"),
                "data": f'"{hex_data}"',
                "height": "0",
                "prove": "false"
            }

            self._debug_log(f"Intent query parameters: {params}")

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    result = await response.json()

                    code, decoded_str, json_value = self._process_response(result)

                    if code == 0 and json_value is not None:
                        return json_value
                    else:
                        self._debug_log(f"Intent query returned code {code}: {decoded_str}")
                        return None
        except Exception as e:
            self._debug_log(f"Error querying intent: {e}")
            return None

    def get_intent(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Get the intent for an address synchronously.

        Args:
            address: Account address to query

        Returns:
            Intent data or None if not found
        """
        return self._run_async(self.get_intent_async(address))

    async def get_aggregate_balances_async(self, addresses: List[str]) -> Dict[str, float]:
        """
        Get aggregated balances across multiple addresses asynchronously.

        This method calculates the sum of token balances across all provided addresses.
        Useful for getting total balances across multiple wallets or accounts.

        Args:
            addresses: List of addresses to aggregate balances for

        Returns:
            Dictionary mapping token symbols to aggregated amounts
        """
        try:
            json_data = json.dumps(addresses)
            hex_data = self._hex_encode_data(json_data)

            url = f"{self.http_url}/abci_query"
            params = {
                "path": json.dumps("/store/aggregate"),
                "data": f'"{hex_data}"',
                "height": "0",
                "prove": "false"
            }

            self._debug_log(f"Aggregate balances query params: {params}")

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    result = await response.json()

                    code, decoded_str, json_value = self._process_response(result)

                    if code != 0:
                        self._debug_log(f"Error querying aggregate balances: {decoded_str}")
                        return {}

                    if json_value is None:
                        return {}

                    if isinstance(json_value, dict):
                        return json_value
                    elif isinstance(json_value, list):
                        balances = {}
                        for item in json_value:
                            if isinstance(item, list) and len(item) == 2:
                                token, amount = item
                                balances[token] = amount
                        return balances
                    else:
                        return {}

        except Exception as e:
            self._debug_log(f"Error getting aggregate balances: {e}")
            return {}

    def get_aggregate_balances(self, addresses: List[str]) -> Dict[str, float]:
        """
        Get aggregated balances across multiple addresses.

        This method calculates the sum of token balances across all provided addresses.
        Useful for getting total balances across multiple wallets or accounts.

        Args:
            addresses: List of addresses to aggregate balances for

        Returns:
            Dictionary mapping token symbols to aggregated amounts
        """
        return self._run_async(self.get_aggregate_balances_async(addresses))

    async def get_all_intents(self) -> Dict[str, Any]:
        """
        Get all intents in the system asynchronously.

        This method queries the node for all registered intents and parses them into
        specialized Intent objects from the SDK. It handles various intent types including
        All, Any, Restriction, Finite, Temporary and Signature intents.

        Returns:
            Dictionary mapping intent identifiers to objects containing:
            - 'intent': Parsed SDK Intent object (if parsing was successful)
            - 'raw_intent': Original JSON intent data
            - 'addresses': List of addresses associated with the intent
            - 'error': Error message (if there was an error parsing)
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
                        self._debug_log(f"Error querying intents: {decoded_str}")
                        return {}

            parsed_intents = {}

            def parse_intent(raw_intent, addresses=None, intent_id=None):
                """Helper function to parse an intent and handle errors"""
                tag = f"intent_{intent_id}" if intent_id is not None else str(raw_intent)
                result = {
                    'intent': None,
                    'raw_intent': raw_intent,
                    'addresses': addresses or []
                }

                # Try to parse the intent if it has a tag
                if isinstance(raw_intent, dict) and 'tag' in raw_intent:
                    try:
                        result['intent'] = Intent.from_json(raw_intent)
                        tag = f"{raw_intent['tag']}_{intent_id}" if intent_id is not None else raw_intent['tag']
                    except Exception as e:
                        self._debug_log(f"Error parsing intent: {e}")
                        result['error'] = str(e)

                # Handle token/amount pairs
                elif (isinstance(raw_intent, list) and len(raw_intent) == 2 and
                      isinstance(raw_intent[0], str) and isinstance(raw_intent[1], (int, float))):
                    token, amount = raw_intent
                    if token in ["BTC", "ETH", "USDC", "USDT", "SALT"]:
                        try:
                            result['intent'] = Restriction(Lit(0), Relation.EQ, Lit(amount))
                            tag = f"TokenBalance_{token}_{intent_id}" if intent_id is not None else f"TokenBalance_{token}"
                        except Exception as e:
                            self._debug_log(f"Error creating token balance for {token}: {e}")
                            result['error'] = str(e)

                return tag, result

            if isinstance(json_value, list):
                self._debug_log(f"Received list of {len(json_value)} intent items")

                for i, intent_item in enumerate(json_value):
                    try:
                        addresses = []
                        raw_intent = None

                        if isinstance(intent_item, list) and len(intent_item) > 0:
                            raw_intent = intent_item[0]
                            if len(intent_item) > 1:
                                addresses = intent_item[1]

                        if isinstance(raw_intent, list):
                            for item in raw_intent:
                                if isinstance(item, dict) and 'tag' in item:
                                        raw_intent = item
                                        break
                        else:
                            raw_intent = intent_item

                        tag, intent_data = parse_intent(raw_intent, addresses, i)
                        parsed_intents[tag] = intent_data

                    except Exception as e:
                        self._debug_log(f"Error parsing intent {i}: {e}")
                        parsed_intents[f"intent_{i}"] = {
                            'intent': None,
                            'raw_intent': intent_item,
                            'error': str(e),
                            'addresses': []
                        }

            elif isinstance(json_value, dict):
                for intent_type, addresses in json_value.items():
                    tag, intent_data = parse_intent(intent_type, addresses)
                    parsed_intents[tag] = intent_data

            return parsed_intents

        except Exception as e:
            self._debug_log(f"Error getting all intents: {e}")
            return {}

    def get_all_intents_sync(self) -> Dict[str, Any]:
        """
        Get all intents in the system.

        This method queries the node for all registered intents and parses them into
        specialized Intent objects from the SDK. It handles various intent types including
        All, Any, Restriction, Finite, Temporary and Signature intents.

        Returns:
            Dictionary mapping intent identifiers to objects containing:
            - 'intent': Parsed SDK Intent object (if parsing was successful)
            - 'raw_intent': Original JSON intent data
            - 'addresses': List of addresses associated with the intent
            - 'error': Error message (if there was an error parsing)
        """
        return self._run_async(self.get_all_intents())

    async def get_wallet_info_async(self, address: str) -> Dict[str, Any]:
        """
        Get wallet information for an address asynchronously.

        This method retrieves comprehensive information about a wallet, including:
        - All token balances
        - The wallet's intent (parsed into an SDK Intent object)

        Args:
            address: Address to get wallet info for

        Returns:
            Dictionary with:
            - "balances": Token balances (as dictionary or list of token/amount pairs)
            - "raw_intent": Original intent data as JSON
            - "sdk_intent": Intent parsed into a specialized SDK Intent object
        """
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
                        self._debug_log(f"Error querying wallet info: {decoded_str}")
                        return {}

                    # Wallet response is a tuple of (balances, intent)
                    # This is represented as a 2-element array in JSON
                    if json_value and isinstance(json_value, list) and len(json_value) == 2:
                        balances = json_value[0]
                        raw_intent = json_value[1]

                        sdk_intent = None
                        if raw_intent and isinstance(raw_intent, dict) and 'tag' in raw_intent:
                            try:
                                sdk_intent = Intent.from_json(raw_intent)
                            except Exception as e:
                                self._debug_log(f"Error parsing intent: {e}")

                        return {
                            "balances": balances,
                            "raw_intent": raw_intent,
                            "sdk_intent": sdk_intent
                        }

                    return {}

        except Exception as e:
            self._debug_log(f"Error getting wallet info: {e}")
            return {}

    def get_wallet_info(self, address: str) -> Dict[str, Any]:
        """
        Get wallet information for an address.

        This method retrieves comprehensive information about a wallet, including:
        - All token balances
        - The wallet's intent (parsed into an SDK Intent object)

        Args:
            address: Address to get wallet info for

        Returns:
            Dictionary with:
            - "balances": Token balances (as dictionary or list of token/amount pairs)
            - "raw_intent": Original intent data as JSON
            - "sdk_intent": Intent parsed into a specialized SDK Intent object
        """
        return self._run_async(self.get_wallet_info_async(address))
