"""
Account management for Saline SDK.

This module provides comprehensive account management for the Saline protocol, 
including both individual subaccounts (key pairs) and multi-account management.
"""

from typing import Optional, Dict, Union
from mnemonic import Mnemonic
from .crypto import (
    derive_master_SK,
    derive_key_from_path
)
from .crypto.bls import BLS

class Subaccount:
    """
    Individual Saline subaccount representing a single key pair.
    Handles cryptographic operations and always derived from an Account.
    """
    
    def __init__(self, private_key_bytes: bytes, public_key_bytes: Optional[bytes] = None, 
                 path: Optional[str] = None, label: Optional[str] = None):
        """
        Initialize a subaccount with private key bytes.
        
        Args:
            private_key_bytes: The private key in bytes
            public_key_bytes: Optional public key bytes (will be derived if not provided)
            path: Optional derivation path
            label: Optional subaccount label
        """
        self.private_key_bytes = private_key_bytes
        self._private_key = BLS.PrivateKey.from_bytes(private_key_bytes)
        
        if public_key_bytes is None:
            self._public_key_bytes = BLS.sk_to_pk(private_key_bytes)
        else:
            self._public_key_bytes = public_key_bytes
            
        self.label = label
        self.path = path
        
    @property
    def public_key(self) -> str:
        """Get the public key as hex string."""
        return self._public_key_bytes.hex()
    
    def sign(self, message: bytes) -> bytes:
        """Sign a message with this subaccount's private key."""
        return BLS.sign(self.private_key_bytes, message)
    
    
    def __str__(self) -> str:
        """String representation of the subaccount."""
        if self.label:
            return f"Subaccount '{self.label}' ({self.public_key[:8]}...{self.public_key[-8:]})"
        else:
            return f"Subaccount {self.public_key[:8]}...{self.public_key[-8:]}"


class Account:
    """
    High-level account management.

    Acts as a container for subaccounts and provides a user-friendly 
    interface for managing keys and performing wallet operations.
    """

    @classmethod
    def create(cls) -> 'Account':
        """Create a new account with a random mnemonic."""
        mnemo = Mnemonic("english")
        mnemonic = mnemo.generate(128)  # 12 words
        return cls.from_mnemonic(mnemonic)

    @classmethod
    def from_mnemonic(cls, mnemonic: str, base_path: str = "m/12381/997") -> 'Account':
        """
        Create an account from a mnemonic phrase.

        Args:
            mnemonic: 24-word mnemonic phrase
            base_path: Optional base path for derivation (default: m/12381/997)

        Returns:
            Account instance
            
        Raises:
            ValueError: If the mnemonic is invalid or the base_path is invalid
        """
        mnemo = Mnemonic("english")
        if not mnemo.check(mnemonic):
            raise ValueError("Invalid mnemonic phrase")
            
        # Validate the base path
        if not base_path.startswith("m/"):
            raise ValueError("Base path must start with 'm/'")
            
        # Simple validation: path must have at least two components: m/coin_type/account
        path_components = base_path.split("/")
        if len(path_components) < 3:
            raise ValueError("Base path must have at least coin type and account components (m/coin_type/account)")
            
        # Validate that each component is numeric except for the first 'm'
        for component in path_components[1:]:
            if not component.isdigit():
                raise ValueError(f"Path component '{component}' is not numeric")

        account = cls()
        account._mnemonic = mnemonic
        account._seed = mnemo.to_seed(mnemonic)
        account.base_path = base_path
        return account

    def __init__(self):
        """Initialize an empty account."""
        self._subaccounts: Dict[str, Subaccount] = {}
        self._mnemonic: Optional[str] = None
        self._seed: Optional[bytes] = None
        self.default_subaccount: Optional[str] = None
        self._next_index = 0
        self.base_path = "m/12381/997"

    def create_subaccount(
        self,
        label: str,
        path: Optional[str] = None
    ) -> Subaccount:
        """
        Create a new subaccount.

        Args:
            label: Subaccount label
            path: Optional derivation path (default: m/12381/997/0/0/{next_index})

        Returns:
            Created subaccount

        Raises:
            ValueError: If account not initialized or name exists
        """
        if self._seed is None:
            raise ValueError("Account not initialized with mnemonic")

        if label in self._subaccounts:
            raise ValueError(f"Subaccount '{label}' already exists")

        # Generate default path if none provided
        if path is None:
            idx = self._next_index
            path = f"{self.base_path}/0/0/{idx}"
            self._next_index += 1

        # Create subaccount
        private_key = derive_key_from_path(self._seed, path)
        subaccount = Subaccount(private_key, path=path, label=label)

        # Store subaccount
        self._subaccounts[label] = subaccount

        # Set as default if first subaccount
        if self.default_subaccount is None:
            self.default_subaccount = label

        return subaccount

    def get_subaccount(self, label: str) -> Subaccount:
        """
        Get a subaccount by label.

        Args:
            label: Subaccount label

        Returns:
            Subaccount instance

        Raises:
            KeyError: If subaccount not found
        """
        if label not in self._subaccounts:
            raise KeyError(f"Subaccount '{label}' not found")
        return self._subaccounts[label]

    def list_subaccounts(self) -> Dict[str, str]:
        """
        Get a list of all subaccounts.

        Returns:
            Dict mapping subaccount names to public keys
        """
        return {label: acc.public_key for label, acc in self._subaccounts.items()}

    def set_default_subaccount(self, label: str) -> None:
        """
        Set the default subaccount.

        Args:
            label: Subaccount label

        Raises:
            KeyError: If subaccount not found
        """
        if label not in self._subaccounts:
            raise KeyError(f"Subaccount '{label}' not found")
        self.default_subaccount = label

    def transfer(
        self,
        to: str,
        amount: Union[int, float],
        currency: str = "USDC",
        from_subaccount: Optional[str] = None
    ) -> bytes:
        """
        Create a transfer transaction.

        Args:
            to: Recipient address (public key)
            amount: Amount to transfer
            currency: Currency to transfer (default: USDC)
            from_subaccount: Source subaccount name (uses default if None)

        Returns:
            Signed transaction

        Raises:
            ValueError: If no source subaccount specified or found
        """
        # Get source subaccount
        if from_subaccount is None:
            if self.default_subaccount is None:
                raise ValueError("No source subaccount specified and no default subaccount set")
            from_subaccount = self.default_subaccount

        subaccount = self.get_subaccount(from_subaccount)
        

        from .transaction.instructions import transfer
        from .transaction.tx import Transaction
        
        transfer_instruction = transfer(
            sender=subaccount.public_key,
            recipient=to,
            token=currency,
            amount=int(amount)
        )
        
        tx = Transaction(instructions=[transfer_instruction])
        tx.set_signer(subaccount.public_key)
        tx.add_intent(subaccount.public_key)
        tx.sign(subaccount)
        
        return tx.serialize_for_network()

    def __getitem__(self, name: str) -> Subaccount:
        """Dict-like access to subaccounts."""
        return self.get_subaccount(name)

    def __contains__(self, name: str) -> bool:
        """Check if subaccount exists."""
        return name in self._subaccounts

    def __iter__(self):
        """Iterate over subaccount names."""
        return iter(self._subaccounts)

    def __len__(self) -> int:
        """Number of subaccounts."""
        return len(self._subaccounts)

    def __str__(self) -> str:
        """String representation."""
        subaccounts = [f"{name}: {acc.public_key}" for name, acc in self._subaccounts.items()]
        default = f" (default: {self.default_subaccount})" if self.default_subaccount else ""
        return f"Account with {len(subaccounts)} subaccounts{default}:\n" + "\n".join(subaccounts)
