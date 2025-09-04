# Alpaca MCP Server

A Model Context Protocol (MCP) server for Alpaca’s Trading API
This lets large language models (LLMs) — like Claude Desktop, Cursor, and VS Code — interact with Alpaca’s trading infrastructure in natural language.

Supports stock trading, options, portfolio management, watchlists, and real-time market data.

## Features

- **Market Data**
  - Real-time quotes, trades, and price bars for stocks
  - Historical price data and trading history
  - Option contract quotes and Greeks (via snapshots)
- **Account Management**
  - View balances, buying power, and account status
  - Inspect all open and closed positions
- **Position Management**
  - Get detailed info on individual holdings
  - Liquidate all or partial positions by share count or percentage
- **Order Management**
  - Place stock and option orders (market or limit)
  - Cancel orders individually or in bulk
  - Retrieve full order history
- **Options Trading**
  - Search and view option contracts by expiration or strike price
  - Place multi-leg options strategies
  - Get latest quotes and Greeks for contracts
- **Market Status & Corporate Actions**
  - Check if markets are open
  - Fetch market calendar and trading sessions
  - View upcoming / historical corporate announcements (earnings, splits, dividends)
- **Watchlist Management**
  - Create, update, and view personal watchlists
  - Manage multiple watchlists for tracking assets
- **Asset Search**
  - Query details for stocks and other Alpaca-supported assets

### Prerequisites

- Python (version requirements can be found at: https://modelcontextprotocol.io/quickstart/server)
- GitHub account
- Alpaca API keys (with paper or live trading access)
- Claude for Desktop or another compatible MCP client


2. Create and activate a virtual environment and Install the required packages:

    **Option A: Using pip (traditional)**

    ```bash
    python3 -m venv myvenv
    source myvenv/bin/activate  # On Windows: myvenv\Scripts\activate
    pip install -r requirements.txt
    ```

    **Option B: Using uv (modern, faster)**

    To use uv, you'll first need to install it. See the [official uv installation guide](https://docs.astral.sh/uv/getting-started/installation/) for detailed installation instructions for your platform.
    ```bash
    uv venv myvenv
    source myvenv/bin/activate # On Windows: myvenv\Scripts\activate
    uv pip install -r requirements.txt
    ```
    **Note:** The virtual environment will use the Python version that was used to create it. If you run the command with Python 3.10 or newer, your virtual environment will also use Python 3.10+. If you want to confirm the version, you can run `python3 --version` after activating the virtual environment. 


