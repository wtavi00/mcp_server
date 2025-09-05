import os
import re
import sys
import time
import argparse
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional, Union

from dotenv import load_dotenv

from alpaca.common.enums import SupportedCurrencies
from alpaca.common.exceptions import APIError
from alpaca.data.enums import DataFeed, OptionsFeed, CorporateActionsType
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.historical.stock import StockHistoricalDataClient, StockLatestTradeRequest
from alpaca.data.historical.corporate_actions import CorporateActionsClient
from alpaca.data.live.stock import StockDataStream
from alpaca.data.requests import (
    OptionLatestQuoteRequest,
    OptionSnapshotRequest,
    Sort,
    StockBarsRequest,
    StockLatestBarRequest,
    StockLatestQuoteRequest,
    StockLatestTradeRequest,
    StockSnapshotRequest,
    StockTradesRequest,
    OptionChainRequest,
    CorporateActionsRequest
)
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import (
    AssetStatus,
    ContractType,
    OrderClass,
    OrderSide,
    OrderType,
    PositionIntent,
    QueryOrderStatus,
    TimeInForce,
)
from alpaca.trading.models import Order
from alpaca.trading.requests import (
    ClosePositionRequest,
    CreateWatchlistRequest,
    GetAssetsRequest,
    GetCalendarRequest,
    GetOptionContractsRequest,
    GetOrdersRequest,
    LimitOrderRequest,
    MarketOrderRequest,
    OptionLegRequest,
    StopLimitOrderRequest,
    StopOrderRequest,
    TrailingStopOrderRequest,
    UpdateWatchlistRequest,
)

from mcp.server.fastmcp import FastMCP

# Configure Python path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
github_core_path = os.path.join(current_dir, '.github', 'core')
if github_core_path not in sys.path:
    sys.path.insert(0, github_core_path)
# Import the UserAgentMixin
from user_agent_mixin import UserAgentMixin
# Define new classes using the mixin
class TradingClientSigned(UserAgentMixin, TradingClient): pass
class StockHistoricalDataClientSigned(UserAgentMixin, StockHistoricalDataClient): pass
class OptionHistoricalDataClientSigned(UserAgentMixin, OptionHistoricalDataClient): pass
class CorporateActionsClientSigned(UserAgentMixin, CorporateActionsClient): pass

def detect_pycharm_environment():
    """
    Detect if we're running in PyCharm using environment variable.
    Set MCP_CLIENT=pycharm in your PyCharm MCP configuration.
    """
    mcp_client = os.getenv("MCP_CLIENT", "").lower()
    return mcp_client == "pycharm"

def parse_arguments():
    """Parse command line arguments for transport configuration."""
    parser = argparse.ArgumentParser(description="Alpaca MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="Transport method to use (default: stdio). Note: WebSocket not supported, use HTTP for remote connections"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind the server to for HTTP/SSE transport (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to for HTTP/SSE transport (default: 8000)"
    )
    return parser.parse_args()

def setup_transport_config(args):
    """Setup transport configuration based on command line arguments."""
    if args.transport == "http":
        return {
            "transport": "http",
            "host": args.host,
            "port": args.port
        }
    elif args.transport == "sse":
        print(f"Warning: SSE transport is deprecated. Consider using HTTP transport instead.")
        return {
            "transport": "sse",
            "host": args.host,
            "port": args.port
        }
    else:
        return {
            "transport": "stdio"
        }

class DefaultArgs:
    def __init__(self):
        self.transport = "stdio"


