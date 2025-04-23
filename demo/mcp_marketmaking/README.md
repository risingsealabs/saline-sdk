
# 🤖 LLM Market Maker on Saline Network

This repo demonstrates how to build a simple, AI-powered market maker using an LLM (like Claude or ChatGPT) connected to the **Saline Network** via **MCP (Machine Control Protocol)** and the **Saline Python SDK**.

You'll be able to:
- Fetch live on-chain intents (limit orders)
- Let your LLM reason about potential matches
- Submit atomic swaps
- All with guardrails enforced by **on-chain mandates** — no smart contracts or vaults required

---

## 📺 Watch First

Before setting this up, we highly recommend watching this short guide on how MCP works and how to wire it up:

▶️ [MCP Intro Video](https://www.youtube.com/watch?v=ww293jeEDT4&t=288s)

---

## 🧪 What You’ll Need

- Python **3.12** (strictly — some MCP features are not compatible with 3.13+)
- A working LLM environment (e.g. Claude Desktop with MCP enabled)
- Some basic Python comfort (or a good ChatGPT prompt 😉)
- [Saline Wallet Testnet(Beta)](https://wallet.try-saline.com) to create/test on-chain mandates
- [Saline SDK Docs](https://saline-sdk.readthedocs.io/en/latest/quickstart.html)

---

## ⚙️ Things to note

### 1. Use virtual environemtn as saline-sdk only support python version < 3.13 so 3.12 is recommended

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


### 4.Sanity check 

```bash
python src/salinetx/server.py
```

Then open your Claude Desktop App — if you see a 🛠 hammer icon, you’re good to go.


## 🧠 Using LLM as a Market Maker

To enable an LLM to match and execute trades on Saline, you'll need to run **two MCP servers**:

### 🔍 1. `query` server
- Allows the LLM to **fetch** all on-chain swap intents
- Think of it as the LLM’s access to the order book

### 📤 2. `submittx` server
- Allows the LLM to **submit** matched transactions
- Used to perform atomic swaps between matching intents

These servers run independently but share logic via the **Saline SDK**.

You can find reference implementations in the `src/` directory:



## ❗ Not a Copy-Paste Template
This repo is meant as a reference, not a one-click starter kit.
MCP setups vary between machines and tools. We recommend:

Watching the video first

Reading through the Saline SDK docs

Using this repo to guide your own custom implementation

