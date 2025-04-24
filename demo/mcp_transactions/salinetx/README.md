# 🚀 Simple Transaction MCP Demo

This demo shows how to use an LLM (like Claude or ChatGPT) to submit **basic on-chain transactions** to the Saline Network using:

- 🧠 **MCP (Machine Control Protocol)**
- 🧰 **Saline Python SDK**
- ⚙️ A single MCP server: `salinetx`

> This setup is ideal for basic operations like transferring funds, testing mandate enforcement, or prototyping an agent wallet.

---

## 📺 Recommended First Step

▶️ [Watch the MCP Setup Video](https://www.youtube.com/watch?v=ww293jeEDT4&t=288s)  
This will help you understand how LLMs can connect to your Python-based backend via MCP.

---

## 🧪 What You’ll Need

- Python **3.12**
- Claude Desktop (or another MCP-compatible LLM)
- [Saline Wallet](https://wallet.try-saline.com) to create/test mandates
- [Saline SDK Docs](https://saline-sdk.readthedocs.io/en/latest/quickstart.html)

---

## ⚙️ Setup Instructions

### 1. Create a Python 3.12 virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 2. Ensure your pyproject.toml or requirements file includes:

```toml
dependencies = [
    "saline-sdk",
    "mcp>=1.6.0"
]
```

### 3.  Install dependencies

```bash
pip install saline-sdk mcp>=1.6.0
# or
poetry install
```

##  🛠 What This Server Does
The salinetx server allows an LLM to:

Construct a transaction (e.g. send 1 ETH from wallet A to B)

Call the Saline SDK to build and submit that transaction

Receive confirmation (or an error) depending on mandate logic

💡 If you’ve installed mandates like "Keep at least 1 BTC", the LLM will be blocked from violating it — the rules live on-chain.