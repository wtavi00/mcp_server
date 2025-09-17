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

## Project Structure

After cloning and activating the virtual environment, your directory structure should look like this:
```
mcp_server/                 ← This is the workspace folder (= project root)
├── alpaca_mcp_server.py    ← Script is directly in workspace root
├── .github/                ← VS Code settings (for VS Code users)
│ ├── core/                 ← Core utility modules
│ └── workflows/            ← GitHub Actions workflows
├── .vscode/                ← VS Code settings (for VS Code users)
│   └── mcp.json
├── venv/                   ← Virtual environment folder
│   └── bin/python
├── .env.example            ← Environment template (use this to create `.env` file)
├── .gitignore              
├── Dockerfile              ← Docker configuration (for Docker use)
├── .dockerignore           ← Docker ignore (for Docker use)
├── requirements.txt           
└── README.md
```
### Create and edit a .env file for your credentials in the project directory

1. Copy the example environment file in the project root by running this command:
   ```bash
   cp .env.example .env
   ```

2. Replace the credentials (e.g. API keys) in the `.env` file:

   ```
   ALPACA_API_KEY = "your_alpaca_api_key_for_paper_account"
   ALPACA_SECRET_KEY = "your_alpaca_secret_key_for_paper_account"
   ALPACA_PAPER_TRADE = True
   TRADE_API_URL = None
   TRDE_API_WSS = None
   DATA_API_URL = None
   STREAM_DATA_WSS = None
   ```
   
### Start the MCP Server

Open a terminal in the project root directory and run the following command:

**For local usage (default - stdio transport):**
```bash
python alpaca_mcp_server.py
```

**For remote usage (HTTP transport):**
```bash
python alpaca_mcp_server.py --transport http
```

**Available transport options:**
- `--transport stdio` (default): Standard input/output for local client connections
- `--transport http`: HTTP transport for remote client connections (default: 127.0.0.1:8000)
- `--transport sse`: Server-Sent Events transport for remote connections (deprecated)
- `--host HOST`: Host to bind the server to for HTTP/SSE transport (default: 127.0.0.1)
- `--port PORT`: Port to bind the server to for HTTP/SSE transport (default: 8000)

**Note:** For more information about MCP transport methods, see the [official MCP transport documentation](https://modelcontextprotocol.io/docs/concepts/transports).

## Claude Desktop Usage

To use Alpaca MCP Server with Claude Desktop, please follow the steps below. The official Claude Desktop setup document is available here: https://modelcontextprotocol.io/quickstart/user

### Configure Claude Desktop

1. Open Claude Desktop
2. Navigate to: `Settings → Developer → Edit Config`
3. Update your `claude_desktop_config.json`:

  **Note:**\
    Replace <project_root> with the path to your cloned alpaca-mcp-server directory. This should point to the Python executable inside the virtual environment you created with `python3 -m venv venv` in the terminal.

**For local usage (stdio transport - recommended):**
```json
{
  "mcpServers": {
    "alpaca": {
      "command": "<project_root>/venv/bin/python",
      "args": [
        "/path/to/alpaca-mcp-server/alpaca_mcp_server.py"
      ],
      "env": {
        "ALPACA_API_KEY": "your_alpaca_api_key_for_paper_account",
        "ALPACA_SECRET_KEY": "your_alpaca_secret_key_for_paper_account"
      }
    }
  }
}
```

**For remote usage (HTTP transport):**
```json
{
  "mcpServers": {
    "alpaca": {
      "transport": "http",
      "url": "http://your-server-ip:8000/mcp",
      "env": {
        "ALPACA_API_KEY": "your_alpaca_api_key_for_paper_account",
        "ALPACA_SECRET_KEY": "your_alpaca_secret_key_for_paper_account"
      }
    }
  }
}
```

## Claude Code Usage

To use Alpaca MCP Server with Claude Code, please follow the steps below.

The `claude mcp add command` is part of [Claude Code](https://www.anthropic.com/claude-code). If you have the Claude MCP CLI tool installed (e.g. by `npm install -g @anthropic-ai/claude-code`), you can use this command to add the server to Claude Code:

```bash
claude mcp add alpaca \
  /path/to/your/alpaca-mcp-server/venv/bin/python \
  /path/to/your/alpaca-mcp-server/alpaca_mcp_server.py \
  -e ALPACA_API_KEY=your_api_key \
  -e ALPACA_SECRET_KEY=your_secret_key
```

**Note:** Replace the paths with your actual project directory paths. This command automatically adds the MCP server configuration to Claude Code without manual JSON editing.

The Claude MCP CLI tool needs to be installed separately. Check following the official pages for availability and installation instructions
* [Learn how to set up MCP with Claude Code](https://docs.anthropic.com/en/docs/claude-code/mcp)
* [Install, authenticate, and start using Claude Code on your development machine](https://docs.anthropic.com/en/docs/claude-code/setup)
