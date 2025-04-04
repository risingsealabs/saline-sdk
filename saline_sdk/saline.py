"""
Main interface to the Saline SDK.

This module provides a web3-like interface for interacting with Saline nodes,
with both synchronous and asynchronous methods.
"""

import asyncio
import json
import time
import logging
from typing import Optional, Union, Dict, List, Any, TypeVar, Callable

from saline_sdk.rpc.client import Client, RPCError, Token
from saline_sdk.account import Account, Subaccount
from saline_sdk.transaction.tx import prepareSimpleTx, encodeSignedTx
from saline_sdk.transaction.bindings import (
    Transaction as BindingsTx, 
    Signed, 
    NonEmpty,
    Send, 
    Receive, 
    Flow,
    SetIntent
)

logger = logging.getLogger(__name__)
T = TypeVar('T')


class Saline:
    """
    Main interface to Saline network.

    Similar to Web3 class in web3.py, this provides the main interface
    for interacting with Saline nodes. Includes both synchronous and
    asynchronous methods for all operations.
    
    The Saline object provides access to the following namespaces:
    - account: Account management (similar to web3.eth.accounts)
    - saline: RPC methods and utilities (similar to web3.eth)
    """

    def __init__(
        self,
        node_url: str = "http://localhost:26657",
        mnemonic: Optional[str] = None,
        debug: bool = False
    ):
        """
        Initialize Saline interface.

        Args:
            node_url: HTTP URL of the Saline node
            mnemonic: Optional mnemonic to initialize account
            debug: Enable debug logging
        """
        self.client = Client(http_url=node_url, debug=debug)

        if mnemonic:
            self.account = Account.from_mnemonic(mnemonic)
        else:
            self.account = Account()
            
    def _get_subaccount_key(self, subaccount: Optional[str] = None) -> str:
        """
        Helper to get a subaccount's public key.
        
        Args:
            subaccount: Subaccount name (uses default if None)
            
        Returns:
            Public key of the subaccount
            
        Raises:
            ValueError: If no subaccount specified and no default set
        """
        if subaccount is None:
            if self.account.default_subaccount is None:
                raise ValueError("No subaccount specified and no default subaccount set")
            subaccount = self.account.default_subaccount
            
        return self.account[subaccount].public_key

    async def is_connected_async(self) -> bool:
        """
        Check if connected to a node asynchronously.
        
        Returns:
            bool: True if connected, False otherwise
        """
        try:
            await self.client.get_status_async()
            return True
        except Exception:
            return False
            
    def is_connected(self) -> bool:
        """
        Check if connected to a node synchronously.
        
        Returns:
            bool: True if connected, False otherwise
        """
        try:
            self.client.get_status()
            return True
        except Exception:
            return False

    def create_account(self) -> str:
        """
        Create a new account with random mnemonic.

        Returns:
            str: Generated mnemonic phrase
        """
        self.account = Account.create()
        return self.account._mnemonic

    def load_account(self, mnemonic: str) -> None:
        """
        Load an account from mnemonic.

        Args:
            mnemonic: Mnemonic phrase
        """
        self.account = Account.from_mnemonic(mnemonic)
        
    def create_subaccount(self, name=None):
        """
        Create a new subaccount under the current account.
        
        Args:
            name: Optional label for the subaccount
            
        Returns:
            The public key of the new subaccount
        """
        return self.account.create_subaccount(label=name)

    def set_default_subaccount(self, name: str) -> None:
        """
        Set the default subaccount.
        
        Args:
            name: Name of the subaccount to set as default
            
        Raises:
            ValueError: If the subaccount doesn't exist
        """
        if name not in self.account.subaccounts:
            raise ValueError(f"Subaccount {name} doesn't exist")
        self.account.default_subaccount = name

    async def get_balance_async(
        self,
        subaccount: Optional[str] = None,
        currency: str = "USDC"
    ) -> Optional[float]:
        """
        Get subaccount balance asynchronously.

        Args:
            subaccount: Subaccount name (uses default if None)
            currency: Currency to check (default: USDC)

        Returns:
            float: Balance amount or None if not found
        """
        public_key = self._get_subaccount_key(subaccount)
        return await self.client.get_balance_async(public_key, currency)
        
    def get_balance(
        self,
        subaccount: Optional[str] = None,
        currency: str = "USDC"
    ) -> Optional[float]:
        """
        Get subaccount balance synchronously.

        Args:
            subaccount: Subaccount name (uses default if None)
            currency: Currency to check (default: USDC)

        Returns:
            float: Balance amount or None if not found
        """
        public_key = self._get_subaccount_key(subaccount)
        return self.client.get_balance(public_key, currency)

    async def get_all_balances_async(
        self,
        subaccount: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Get all balances for a subaccount asynchronously.

        Args:
            subaccount: Subaccount name (uses default if None)

        Returns:
            Dict[str, float]: Dictionary mapping currency symbols to balance amounts
        """
        public_key = self._get_subaccount_key(subaccount)
        return await self.client.get_all_balances_async(public_key)
        
    def get_all_balances(
        self,
        subaccount: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Get all balances for a subaccount synchronously.

        Args:
            subaccount: Subaccount name (uses default if None)

        Returns:
            Dict[str, float]: Dictionary mapping currency symbols to balance amounts
        """
        public_key = self._get_subaccount_key(subaccount)
        return self.client.get_all_balances(public_key)
        
    async def get_aggregate_balances_async(
        self,
        subaccounts: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Get aggregate balances across multiple subaccounts asynchronously.
        
        Args:
            subaccounts: List of subaccount names (uses all if None)
            
        Returns:
            Dict[str, float]: Dictionary mapping currency symbols to balance amounts
        """
        if subaccounts is None:
            subaccounts = list(self.account.subaccounts.keys())
            
        addresses = [self.account[name].public_key for name in subaccounts]
        return await self.client.get_aggregate_balances_async(addresses)
        
    def get_aggregate_balances(
        self,
        subaccounts: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Get aggregate balances across multiple subaccounts synchronously.
        
        Args:
            subaccounts: List of subaccount names (uses all if None)
            
        Returns:
            Dict[str, float]: Dictionary mapping currency symbols to balance amounts
        """
        if subaccounts is None:
            subaccounts = list(self.account.subaccounts.keys())
            
        addresses = [self.account[name].public_key for name in subaccounts]
        return self.client.get_aggregate_balances(addresses)

    async def get_intent_async(
        self,
        subaccount: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get intent for a subaccount asynchronously.

        Args:
            subaccount: Subaccount name (uses default if None)

        Returns:
            Dict[str, Any]: Intent data or None if not found
        """
        public_key = self._get_subaccount_key(subaccount)
        return await self.client.get_intent_async(public_key)
        
    def get_intent(
        self,
        subaccount: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get intent for a subaccount synchronously.

        Args:
            subaccount: Subaccount name (uses default if None)

        Returns:
            Dict[str, Any]: Intent data or None if not found
        """
        public_key = self._get_subaccount_key(subaccount)
        return self.client.get_intent(public_key)
        
    async def get_all_intents_async(self) -> Dict[str, Any]:
        """
        Get all intents in the system asynchronously.
        
        Returns:
            Dict[str, Any]: Dictionary mapping addresses to intent data
        """
        return await self.client.get_all_intents()
        
    def get_all_intents(self) -> Dict[str, Any]:
        """
        Get all intents in the system synchronously.
        
        Returns:
            Dict[str, Any]: Dictionary mapping addresses to intent data
        """
        return self.client.get_all_intents_sync()
        
    async def get_wallet_info_async(
        self,
        subaccount: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get wallet information for a subaccount asynchronously.
        
        Args:
            subaccount: Subaccount name (uses default if None)
            
        Returns:
            Dict[str, Any]: Wallet information including balances and intent
        """
        public_key = self._get_subaccount_key(subaccount)
        return await self.client.get_wallet_info_async(public_key)
        
    def get_wallet_info(
        self,
        subaccount: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get wallet information for a subaccount synchronously.
        
        Args:
            subaccount: Subaccount name (uses default if None)
            
        Returns:
            Dict[str, Any]: Wallet information including balances and intent
        """
        public_key = self._get_subaccount_key(subaccount)
        return self.client.get_wallet_info(public_key)
        
    async def get_current_block_async(self) -> Dict[str, Any]:
        """
        Get the latest block data asynchronously.
        
        Returns:
            Dict[str, Any]: Current block data
        """
        return await self.client.get_current_block()
        
    def get_current_block(self) -> Dict[str, Any]:
        """
        Get the latest block data synchronously.
        
        Returns:
            Dict[str, Any]: Current block data
        """
        return self.client.get_current_block_sync()
        
    async def get_block_async(self, height: Optional[int] = None) -> Dict[str, Any]:
        """
        Get block by height asynchronously.
        
        Args:
            height: Block height (defaults to latest block)
            
        Returns:
            Dict[str, Any]: Block data
        """
        return await self.client.get_block(height)
        
    def get_block(self, height: Optional[int] = None) -> Dict[str, Any]:
        """
        Get block by height synchronously.
        
        Args:
            height: Block height (defaults to latest block)
            
        Returns:
            Dict[str, Any]: Block data
        """
        return self.client.get_block_sync(height)
        
    async def get_transactions_async(self, height: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get transactions at a specific block height asynchronously.
        
        Args:
            height: Block height (defaults to latest block)
            
        Returns:
            List[Dict[str, Any]]: List of transactions
        """
        return await self.client.get_transactions(height)
        
    def get_transactions(self, height: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get transactions at a specific block height synchronously.
        
        Args:
            height: Block height (defaults to latest block)
            
        Returns:
            List[Dict[str, Any]]: List of transactions
        """
        return self.client.get_transactions_sync(height)
        
    async def get_transaction_async(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get transaction by hash asynchronously.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Dict[str, Any]: Transaction data
        """
        return await self.client.get_tx(tx_hash)
        
    def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get transaction by hash synchronously.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Dict[str, Any]: Transaction data
        """
        return self.client.get_tx_sync(tx_hash)

    async def send_transaction_async(
        self,
        transaction: Union[Dict[str, Any], BindingsTx, str, bytes],
        from_subaccount: Optional[str] = None,
        wait_for_confirmation: bool = True
    ) -> dict:
        """
        Send a transaction to the network asynchronously.
        
        Args:
            transaction: Transaction data (can be dict, Transaction object, bytes, or encoded string)
            from_subaccount: Source subaccount (uses default if None)
            wait_for_confirmation: Whether to wait for confirmation
            
        Returns:
            Dict[str, Any]: Transaction result
            
        Raises:
            ValueError: If transaction format is invalid
        """
        # Get the subaccount to use
        if from_subaccount is None:
            if self.account.default_subaccount is None:
                raise ValueError("No subaccount specified and no default subaccount set")
            from_subaccount = self.account.default_subaccount
            
        subaccount = self.account[from_subaccount]
        
        # Prepare transaction if it's a dict or Transaction object
        if isinstance(transaction, dict) or isinstance(transaction, BindingsTx):
            # Convert to Transaction object if it's a dict
            if isinstance(transaction, dict):
                from saline_sdk.transaction.tx import Transaction
                transaction = Transaction(**transaction)
                
            # Sign the transaction
            transaction = prepareSimpleTx(subaccount, transaction)
        
        # For bytes, encode to base64
        elif isinstance(transaction, bytes):
            import base64
            transaction = base64.b64encode(transaction).decode('ascii')
            
        # Validate string is a valid base64 encoding
        elif isinstance(transaction, str):
            try:
                import base64
                base64.b64decode(transaction)
            except:
                raise ValueError("String transaction must be base64 encoded")
                
        # Send the transaction
        logger.debug(f"Sending transaction to blockchain...")
        
        if wait_for_confirmation:
            result = await self.client.tx_commit(transaction)
        else:
            result = await self.client.tx_broadcast(transaction)
            
        logger.debug(f"Transaction result: {result}")
        
        # Wait for confirmation if requested
        if wait_for_confirmation and 'hash' in result:
            receipt = await self.wait_for_transaction_receipt_async(result['hash'])
            if receipt:
                result['receipt'] = receipt
                
        return result
        
    def send_transaction(
        self,
        transaction: Union[Dict[str, Any], BindingsTx, str, bytes],
        from_subaccount: Optional[str] = None,
        wait_for_confirmation: bool = True
    ) -> dict:
        """
        Send a transaction to the network synchronously.
        
        Args:
            transaction: Transaction data (can be dict, Transaction object, bytes, or encoded string)
            from_subaccount: Source subaccount (uses default if None)
            wait_for_confirmation: Whether to wait for confirmation
            
        Returns:
            Dict[str, Any]: Transaction result
        """
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                self.send_transaction_async(transaction, from_subaccount, wait_for_confirmation)
            )
        finally:
            loop.close()

    async def wait_for_transaction_receipt_async(
        self,
        tx_hash: str,
        timeout: int = 120,
        poll_interval: float = 0.1
    ) -> Optional[dict]:
        """
        Wait for a transaction receipt asynchronously.
        
        Args:
            tx_hash: Transaction hash
            timeout: Maximum time to wait in seconds
            poll_interval: Time between polling attempts in seconds
            
        Returns:
            Optional[Dict[str, Any]]: Transaction receipt or None if not found within timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                tx_data = await self.client.get_tx(tx_hash)
                if tx_data:
                    return tx_data
            except RPCError:
                pass  # Continue polling
                
            await asyncio.sleep(poll_interval)
            
        return None
        
    def wait_for_transaction_receipt(
        self,
        tx_hash: str,
        timeout: int = 120,
        poll_interval: float = 0.1
    ) -> Optional[dict]:
        """
        Wait for a transaction receipt synchronously.
        
        Args:
            tx_hash: Transaction hash
            timeout: Maximum time to wait in seconds
            poll_interval: Time between polling attempts in seconds
            
        Returns:
            Optional[Dict[str, Any]]: Transaction receipt or None if not found within timeout
        """
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                self.wait_for_transaction_receipt_async(tx_hash, timeout, poll_interval)
            )
        finally:
            loop.close()
            
    def transfer(
        self,
        to: str,
        amount: Union[int, float],
        currency: str = "USDC",
        from_subaccount: Optional[str] = None,
        wait_for_confirmation: bool = True
    ) -> dict:
        """
        Transfer funds from one account to another.
        
        This is a convenience method that creates and sends a transfer transaction.
        
        Args:
            to: Recipient address
            amount: Amount to transfer
            currency: Currency to transfer (default: USDC)
            from_subaccount: Source subaccount (uses default if None)
            wait_for_confirmation: Whether to wait for confirmation
            
        Returns:
            Dict[str, Any]: Transaction result
        """
        from saline_sdk.transaction.bindings import TransferFunds
        
        # Create the transaction
        transfer_instruction = TransferFunds(
            source=self._get_subaccount_key(from_subaccount),
            target=to,
            funds={currency: amount}
        )
        
        tx = BindingsTx(instructions=NonEmpty.from_list([transfer_instruction]))
        
        # Send the transaction
        return self.send_transaction(
            tx, 
            from_subaccount=from_subaccount,
            wait_for_confirmation=wait_for_confirmation
        )

    def set_intent(
        self,
        intent: Any,
        subaccount: Optional[str] = None,
        wait_for_confirmation: bool = True
    ) -> dict:
        """
        Set an intent for a subaccount.
        
        Args:
            intent: Intent object
            subaccount: Subaccount name (uses default if None)
            wait_for_confirmation: Whether to wait for confirmation
            
        Returns:
            Dict[str, Any]: Transaction result
        """
        # Create the transaction
        set_intent_instruction = SetIntent(
            host=self._get_subaccount_key(subaccount),
            intent=intent
        )
        
        tx = BindingsTx(instructions=NonEmpty.from_list([set_intent_instruction]))
        
        # Send the transaction
        return self.send_transaction(
            tx, 
            from_subaccount=subaccount,
            wait_for_confirmation=wait_for_confirmation
        )

    def create_swap_intent(
        self,
        give_token: str,
        give_amount: Union[int, float],
        want_token: str,
        want_amount: Union[int, float]
    ) -> Any:
        """
        Create a swap intent.
        
        Args:
            give_token: Token to give
            give_amount: Amount to give
            want_token: Token to receive
            want_amount: Amount to receive
            
        Returns:
            Intent object representing the swap
            
        Example:
            >>> saline = Saline()
            >>> intent = saline.create_swap_intent("USDC", 10, "BTC", 0.001)
            >>> saline.set_intent(intent, "my_account")
        """
        # Use the operator syntax for creating swap intents
        return Send(Flow(None, Token[give_token])) * give_amount <= Receive(Flow(None, Token[want_token])) * want_amount
    
    def find_matching_swaps(
        self, 
        give_token: Optional[str] = None,
        want_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find matching swap intents in the system.
        
        Args:
            give_token: Token to give (optional filter)
            want_token: Token to receive (optional filter)
            
        Returns:
            List of matching swap intents
            
        Example:
            >>> saline = Saline()
            >>> swaps = saline.find_matching_swaps("USDC", "BTC")
            >>> for swap in swaps:
            ...     print(f"Found swap: {swap['give_amount']} {swap['give_token']} for {swap['want_amount']} {swap['want_token']}")
        """
        # Get all intents in the system
        all_intents = self.get_all_intents()
        matching_swaps = []
        
        # Process each intent to find swaps
        for address, intent_data in all_intents.items():
            # Skip if no intent data
            if not intent_data:
                continue
                
            # Get the raw intent
            raw_intent = intent_data.get("raw_intent", {})
            
            # Function to recursively extract swap details from intent nodes
            def extract_swap_from_node(node):
                if not isinstance(node, dict):
                    return None
                
                # Check for a restriction with send/receive pattern
                if node.get("tag") == "Restriction":
                    lhs = node.get("lhs", {})
                    rhs = node.get("rhs", {})
                    relation = node.get("relation")
                    
                    # Check if it's a swap intent (Send <= Receive)
                    if (lhs.get("tag") == "Send" and 
                        rhs.get("tag") == "Receive" and 
                        relation == "LE"):
                        
                        g_token = lhs.get("flow", {}).get("token")
                        w_token = rhs.get("flow", {}).get("token")
                        
                        # Filter by token if specified
                        if ((give_token and g_token != give_token) or 
                            (want_token and w_token != want_token)):
                            return None
                            
                        # Get amounts
                        g_amount = lhs.get("amount", 1)
                        if isinstance(g_amount, dict) and g_amount.get("tag") == "Lit":
                            g_amount = g_amount.get("value", 1)
                            
                        w_amount = rhs.get("amount", 1)
                        if isinstance(w_amount, dict) and w_amount.get("tag") == "Lit":
                            w_amount = w_amount.get("value", 1)
                        
                        return {
                            "address": address,
                            "give_token": g_token,
                            "give_amount": g_amount,
                            "want_token": w_token,
                            "want_amount": w_amount,
                            "rate": float(g_amount) / float(w_amount) if w_amount else 0
                        }
                
                # Check children for compound intents
                if "children" in node:
                    for child in node.get("children", []):
                        result = extract_swap_from_node(child)
                        if result:
                            return result
                
                return None
            
            # Process raw intent
            if isinstance(raw_intent, dict):
                swap = extract_swap_from_node(raw_intent)
                if swap:
                    matching_swaps.append(swap)
            elif isinstance(raw_intent, list) and len(raw_intent) > 1:
                conditions = raw_intent[1]
                if isinstance(conditions, dict):
                    swap = extract_swap_from_node(conditions)
                    if swap:
                        matching_swaps.append(swap)
        
        return matching_swaps
    
    def fulfill_swap(
        self,
        swap1: Dict[str, Any],
        swap2: Dict[str, Any],
        from_subaccount: Optional[str] = None,
        wait_for_confirmation: bool = True
    ) -> Dict[str, Any]:
        """
        Fulfill a swap between two intents.
        
        Args:
            swap1: First swap intent
            swap2: Second swap intent
            from_subaccount: Source subaccount for signing (uses default if None)
            wait_for_confirmation: Whether to wait for confirmation
            
        Returns:
            Dict[str, Any]: Transaction result
            
        Example:
            >>> saline = Saline()
            >>> swaps = saline.find_matching_swaps("USDC", "BTC")
            >>> if len(swaps) >= 2:
            ...     result = saline.fulfill_swap(swaps[0], swaps[1])
            ...     print(f"Swap fulfilled: {result}")
        """
        from saline_sdk.transaction.bindings import TransferFunds
        
        # Create transfer instructions
        instruction1 = TransferFunds(
            source=swap1["address"],
            target=swap2["address"],
            funds={swap1["give_token"]: swap1["give_amount"]}
        )
        
        instruction2 = TransferFunds(
            source=swap2["address"],
            target=swap1["address"],
            funds={swap2["give_token"]: swap2["give_amount"]}
        )
        
        # Create the transaction
        tx = BindingsTx(instructions=NonEmpty.from_list([instruction1, instruction2]))
        
        # Send the transaction
        return self.send_transaction(
            tx,
            from_subaccount=from_subaccount,
            wait_for_confirmation=wait_for_confirmation
        )

    def __str__(self) -> str:
        """String representation of the Saline interface."""
        return f"Saline(node_url={self.client.http_url}, " \
               f"account={str(self.account) if hasattr(self, 'account') else 'None'})"
