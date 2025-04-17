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

1. Set up your Python 3.12 virtual environment:

   .. code-block:: bash

       python3.12 -m venv venv
       source venv/bin/activate
       pip install --upgrade pip



2. Install the SDK using pip:

   .. code-block:: bash

       pip install saline-sdk

3. Initialize the SDK with your node URL:

   .. code-block:: python

    import asyncio
    from saline_sdk import Client

    async def main():
        client = Client(http_url="https://node0.try-saline.com")
        try:
            status = await client.get_status()  # Await the async function
            print(f"Connected to node: {status['node_info']['moniker']} @ {status['node_info']['network']} (Block: {status['sync_info']['latest_block_height']})")
        except Exception as e:
            print(f"Failed to connect or get status: {e}")

    if __name__ == "__main__":
        asyncio.run(main())


4. See the :doc:`quickstart` guide for more detailed instructions.

Version Compatibility
-------------------
Requires Python 3.12 (any minor version), i.e., Python ≥3.12.0 and <3.13.
Designed to work with Saline nodes running version ≥ 0.1.0.
