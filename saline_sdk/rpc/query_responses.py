"""
Dataclasses for structured RPC query responses, using bindings.py types for intents.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
import saline_sdk.transaction.bindings as bindings
import json # Add import for json.dumps
import logging

logger = logging.getLogger(__name__)

@dataclass
class ParsedIntentInfo:
    """Holds information about a single intent fetched from the node."""
    intent_id: str
    parsed_intent: Optional[bindings.Intent]
    addresses: List[List[str]] = field(default_factory=list) # Raw address list
    raw_intent_data: Any = None # Keep raw data for debugging
    error: Optional[str] = None # Parsing error message

@dataclass
class ParsedAllIntentsResponse:
    """Wrapper for the result of get_all_intents."""
    intents: Dict[str, ParsedIntentInfo] = field(default_factory=dict)

@dataclass
class ParsedWalletInfo:
    """Structure holding parsed info from get_wallet_info."""
    address: str
    balances: Dict[str, int] = field(default_factory=dict) # Assuming token -> amount mapping
    parsed_intent: Optional[bindings.Intent] = None
    raw_wallet_data: Any = None # Keep raw data for debugging/completeness
    error: Optional[str] = None # Parsing error message

# --- Optimized Helper Functions for Analyzing Parsed Bindings ---

# Dictionary mapping composite types to the names of attributes holding sub-nodes
_RECURSION_ATTR_MAP = {
    bindings.All: ('children',),
    bindings.Any: ('children',),
    bindings.Restriction: ('lhs', 'rhs'),
    bindings.Finite: ('inner',),
    bindings.Temporary: ('inner',),
    bindings.Arithmetic2: ('lhs', 'rhs'),
    # Note: bindings.Var is treated as a leaf
}

def contains_binding_type(node: Optional[Union[bindings.Intent, bindings.Expr]], target_type: type) -> bool:
    """(Optimized) Recursively check if an intent/expression tree contains a node of target_type."""
    if node is None:
        return False
    if isinstance(node, target_type):
        return True

    node_type = node.__class__
    if node_type in _RECURSION_ATTR_MAP:
        for attr_name in _RECURSION_ATTR_MAP[node_type]:
            # Get the attribute value (could be a single node or a list)
            child_or_children = getattr(node, attr_name, None)

            if isinstance(child_or_children, list):
                # If it's a list, check if any child contains the target type
                if any(contains_binding_type(child, target_type) for child in child_or_children):
                    return True
            elif child_or_children is not None:
                # If it's a single node, recurse
                if contains_binding_type(child_or_children, target_type):
                    return True

    # If we reach here, the target type wasn't found directly or in descendants
    return False


def parse_dict_to_binding_intent(raw_intent_data: Any) -> Optional[bindings.Intent]:
    """
    Attempts to parse a raw dictionary/list structure into an Intent object
    from bindings.py using its from_json methods.

    Handles potential nesting in the raw data.
    Returns None if parsing fails or input is invalid.
    """
    intent_dict = None
    # Extract the actual intent dictionary from potential nesting
    # Common patterns observed: [[{...}]], [{...}], {...}
    if isinstance(raw_intent_data, list) and raw_intent_data:
        first_item = raw_intent_data[0]
        if isinstance(first_item, list) and first_item:
            if isinstance(first_item[0], dict):
                intent_dict = first_item[0]
        elif isinstance(first_item, dict):
            intent_dict = first_item
    elif isinstance(raw_intent_data, dict):
        intent_dict = raw_intent_data

    if not intent_dict or 'tag' not in intent_dict:
        print(f"DEBUG: Could not find valid intent dict with tag in {raw_intent_data}")
        return None

    try:
        return bindings.Intent.from_json(intent_dict)
    except Exception as e:
        logger.error(f"Error during bindings.Intent.from_json: {e!r}", exc_info=True)
        try:
             logger.error(f"Failed processing dict: {json.dumps(intent_dict)}")
        except TypeError:
             logger.error(f"Failed processing dict (non-serializable?): {intent_dict}")
        return None