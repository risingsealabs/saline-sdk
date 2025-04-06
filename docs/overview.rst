========
Overview
========

Saline SDK provides a comprehensive interface for interacting with the Saline blockchain network.
It is designed to be easy to use while providing powerful features for developers building on the Saline platform.

Key Features
-----------

* **Comprehensive Account Management**: Create, import, and manage accounts with BLS key pairs
* **Transaction Management**: Create, sign, and send transactions with ease
* **RPC Client**: Interact with Saline nodes via secure JSON-RPC
* **Async Support**: Full asynchronous API for high-performance applications
* **Token Support**: Built-in support for USDC, BTC, ETH, and other tokens
* **Web3-like Interface**: Familiar API for blockchain developers

Getting Started
--------------

To start using the Saline SDK, follow these steps:

1. Install the SDK using pip:

   .. code-block:: bash

       pip install saline-sdk

2. Initialize the SDK with your node URL:

   .. code-block:: python

       from saline_sdk import Client

       # Connect to a Saline node using the http_url parameter
       client = Client(http_url=\"https://node0.try-saline.com\")

       # Check connection by calling get_status()
       try:
           status = client.get_status() # Synchronous call
                   print(f"Connected to node: {status['node_info']['moniker']} @ {status['node_info']['network']} (Block: {status['sync_info']['latest_block_height']})")
['latest_block_height']})")
       except Exception as e:
           print(f"Failed to connect or get status: {e}")

3. See the :doc:`quickstart` guide for more detailed instructions.

Version Compatibility
-------------------

The Saline SDK requires Python 3.12 or higher. It is designed to work with Saline nodes running version 0.1.0 and above.