========
Demo
========

This section highlights real-world demonstrations of how Saline SDK enables powerful asset protection through programmable mandates.
Each demo includes:

• A clear use case

• A YouTube walkthrough

• GitHub code for replication

.. note::
These examples go beyond basic scripts. They showcase how Saline protects assets from AI hallucinated or rogue agents, matchers, or bots, ensuring safe automation on and across chains.

.. _demo_block_asset:

Block Assets from Agent
=========================

Block Assets from Being Used by Agent

Purpose:
Prevent an unauthorized matcher/agent from touching user assets—even if it submits a valid-looking transaction.

.. raw:: html

   <iframe width="560" height="315" src="https://www.youtube.com/embed/oIpoWj73Hj0" 
           title="Block assets from being used by Agent/Matcher (SDK)" frameborder="0" allowfullscreen></iframe>

💻 Code: `GitHub Source <https://github.com/risingsealabs/saline-sdk/blob/main/demo/whitelist-agents>`_

Scenario:

    • User A installs a mandates that restrcit its BTC balance to only stay above 3 

    • Matcher A attempts to transfer 1 BTC → ❌ REJECTED

    • Matcher A transfers 2 ETH → ✅ ACCEPTED

Insight:
Even if the matcher is allowed to interact generally, fine-grained mandates on assets can override it.



.. _demo_whitelist_agents:

Only Allow Interaction with Whitelisted Agents
=========================

Only Allow Interaction with Whitelisted Agents

Purpose:
Only trusted agents/LLMs should be allowed to interact with your wallet.

.. raw:: html

   <iframe width="560" height="315" src="https://www.youtube.com/embed/oIpoWj73Hj0" 
           title="Only allow interaction with whitelist Agent/Matcher (SDK)" frameborder="0" allowfullscreen></iframe>


💻 Code: `GitHub Source <https://github.com/risingsealabs/saline-sdk/blob/main/demo/whitelist-agents>`_

Scenario:

    • User B creates a mandate that whitelists only Matcher/Agent XYZ.

    • Agent XYZ transfers ETH/BTC from User B address  → ✅ ACCEPTED

    • Any other agent attempt to transfer asset from User B → ❌ REJECTED

Insight:
Whitelisting agents gives users powerful filters for automation and delegation.



.. _demo_swap_conditions:

Conditional Swap, Whitelist and Time-frame
=========================

Conditional Swap: 1 BTC for >= 20 ETH + Only With ABC Agent + Allow once

Purpose:
Showcase conditional, chained logic for automated swaps.

.. raw:: html

   <iframe width="560" height="315" src="https://www.youtube.com/embed/CB3ghYoFQBc" 
           title="Complex Multi-Layer rules for agent interaction (SDK)" frameborder="0" allowfullscreen></iframe>

💻 Code: `GitHub Source <https://github.com/risingsealabs/saline-sdk/blob/main/demo/swap_whitelist_timeframe>`_

Scenario:

    • User C creates an intent: "Only swap 1 BTC for ETH >= 20, agent must be ABC and allow once"

    • Matcher ABC proposes 2 BTC → ❌ REJECTED
    
    • Matcher XYZ proposes 1 BTC for 20 ETH → ❌ REJECTED

    • Matcher ABC proposes 1 BTC for 20 ETH → ✅ ACCEPTED

Insight:
Saline lets you specify not just what to trade, but under what logic, with whom and how many time .

.. _demo_mcp_guard:
LLM Agent With Mandate Awareness (MCP)
=========================

Purpose:
Demonstrate how a language model connected via MCP can understand and respect user mandates.

.. raw:: html

   <iframe width="560" height="315" src="https://www.youtube.com/embed/U3MJu-eW6Rc" 
           title="Submit transaction through LLM with MCP using mandates" frameborder="0" allowfullscreen></iframe>

💻 Code: `GitHub Source <https://github.com/risingsealabs/saline-sdk/blob/main/demo/mcp_transactions>`_

Scenario:

    • User D sets a mandate: "BTC balance must stay >= 2 BTC"

    • LLM Agent attempts 1 BTC transfer → ❌ REJECTED

    • LLM Agent attempts 2 ETH transfer → ✅ ACCEPTED

Insight:
Saline makes mandates legible to agents—enabling verifiable AI compliance.

.. _demo_mcp_swap_matcher:

LLM Matcher market-making with MCP
=========================

LLM Matcher: Discover + Submit Matching Swaps (MCP)

Purpose:
Show how an LLM can act as a decentralized market maker by reading intents, finding matches, and submitting a transaction.

.. raw:: html

   <iframe width="560" height="315" src="https://www.youtube.com/embed/cCRNxDLHXDI" 
           title="Market making intents through LLM with MCP" frameborder="0" allowfullscreen></iframe>

💻 Code: `GitHub Source <https://github.com/risingsealabs/saline-sdk/blob/main/demo/mcp_marketmaking>`_
Scenario:

    • LLM queries all swap intents on-chain

    • Finds compatible pairs

    • Submits atomic transaction to execute both sides

Insight:
This is decentralized, intelligent market-making. No smart contract needed. Just logic and trustless coordination.

.. seealso::
See the `Examples folder on GitHub <https://github.com/risingsealabs/saline-sdk/tree/main/examples>`_ for source code.



