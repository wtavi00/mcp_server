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

args = DefaultArgs()

is_pycharm = detect_pycharm_environment()
log_level = "ERROR" if is_pycharm else "INFO"
if not is_pycharm and __name__ == "__main__":
    print(f"MCP Server starting with transport={args.transport}, log_level={log_level} (PyCharm detected: {is_pycharm})")

mcp = FastMCP("alpaca-trading", log_level=log_level)

load_dotenv()
TRADE_API_KEY = os.getenv("ALPACA_API_KEY")
TRADE_API_SECRET = os.getenv("ALPACA_SECRET_KEY")
ALPACA_PAPER_TRADE = os.getenv("ALPACA_PAPER_TRADE", "True")
TRADE_API_URL = os.getenv("TRADE_API_URL")
TRDE_API_WSS = os.getenv("TRDE_API_WSS")
DATA_API_URL = os.getenv("DATA_API_URL")
STREAM_DATA_WSS = os.getenv("STREAM_DATA_WSS")

if not TRADE_API_KEY or not TRADE_API_SECRET:
    raise ValueError("Alpaca API credentials not found in environment variables.")
    
trade_client = TradingClientSigned(TRADE_API_KEY, TRADE_API_SECRET, paper=ALPACA_PAPER_TRADE)

stock_historical_data_client = StockHistoricalDataClientSigned(TRADE_API_KEY, TRADE_API_SECRET)

stock_data_stream_client = StockDataStream(TRADE_API_KEY, TRADE_API_SECRET, url_override=STREAM_DATA_WSS)

option_historical_data_client = OptionHistoricalDataClientSigned(api_key=TRADE_API_KEY, secret_key=TRADE_API_SECRET)

corporate_actions_client = CorporateActionsClientSigned(api_key=TRADE_API_KEY, secret_key=TRADE_API_SECRET)

# ==============================#
#   Account Information Tools   #
# ==============================#

@mcp.tool()
async def get_account_info() -> str:
    """
    Retrieves and formats the current account information including balances and status.
    
    Returns:
        str: Formatted string containing account details including:
            - Account ID
            - Status
            - Currency
            - Buying Power
            - Cash Balance
            - Portfolio Value
            - Equity
            - Market Values
            - Pattern Day Trader Status
            - Day Trades Remaining
    """
    account = trade_client.get_account()
    
    info = f"""
            Account Information:
            -------------------
            Account ID: {account.id}
            Status: {account.status}
            Currency: {account.currency}
            Buying Power: ${float(account.buying_power):.2f}
            Cash: ${float(account.cash):.2f}
            Portfolio Value: ${float(account.portfolio_value):.2f}
            Equity: ${float(account.equity):.2f}
            Long Market Value: ${float(account.long_market_value):.2f}
            Short Market Value: ${float(account.short_market_value):.2f}
            Pattern Day Trader: {'Yes' if account.pattern_day_trader else 'No'}
            Day Trades Remaining: {account.daytrade_count if hasattr(account, 'daytrade_count') else 'Unknown'}
            """
    return info

@mcp.tool()
async def get_positions() -> str:
    """
    Retrieves and formats all current positions in the portfolio.
    
    Returns:
        str: Formatted string containing details of all open positions including:
            - Symbol
            - Quantity
            - Market Value
            - Average Entry Price
            - Current Price
            - Unrealized P/L
    """
    positions = trade_client.get_all_positions()

    if not positions:
        return "No open positions found."
    
    result = "Current Positions:\n-------------------\n"
    for position in positions:
        result += f"""
                    Symbol: {position.symbol}
                    Quantity: {position.qty} shares
                    Market Value: ${float(position.market_value):.2f}
                    Average Entry Price: ${float(position.avg_entry_price):.2f}
                    Current Price: ${float(position.current_price):.2f}
                    Unrealized P/L: ${float(position.unrealized_pl):.2f} ({float(position.unrealized_plpc) * 100:.2f}%)
                    -------------------
                    """
    return result

@mcp.tool()
async def get_open_position(symbol: str) -> str:
    """
    Retrieves and formats details for a specific open position.
    
    Args:
        symbol (str): The symbol name of the asset to get position for (e.g., 'AAPL', 'MSFT')
    
    Returns:
        str: Formatted string containing the position details or an error message
    """
    try:
        position = trade_client.get_open_position(symbol)

        is_option = len(symbol) > 6 and any(c in symbol for c in ['C', 'P'])
        
        # Format quantity based on asset type
        quantity_text = f"{position.qty} contracts" if is_option else f"{position.qty}"

        return f"""
                Position Details for {symbol}:
                ---------------------------
                Quantity: {quantity_text}
                Market Value: ${float(position.market_value):.2f}
                Average Entry Price: ${float(position.avg_entry_price):.2f}
                Current Price: ${float(position.current_price):.2f}
                Unrealized P/L: ${float(position.unrealized_pl):.2f}
                """ 
    except Exception as e:
        return f"Error fetching position: {str(e)}"

# ============================================================================
# Market Data Tools
# ============================================================================

@mcp.tool()
async def get_stock_quote(symbol: str) -> str:
    """
    Retrieves and formats the latest quote for a stock.
    
    Args:
        symbol (str): Stock ticker symbol (e.g., AAPL, MSFT)
    
    Returns:
        str: Formatted string containing:
            - Ask Price
            - Bid Price
            - Ask Size
            - Bid Size
            - Timestamp
    """
    
    try:
        request_params = StockLatestQuoteRequest(symbol_or_symbols=symbol)
        quotes = stock_historical_data_client.get_stock_latest_quote(request_params)
        
        if symbol in quotes:
            quote = quotes[symbol]
            return f"""
                    Latest Quote for {symbol}:
                    ------------------------
                    Ask Price: ${quote.ask_price:.2f}
                    Bid Price: ${quote.bid_price:.2f}
                    Ask Size: {quote.ask_size}
                    Bid Size: {quote.bid_size}
                    Timestamp: {quote.timestamp}
                    """ 
        else:
            return f"No quote data found for {symbol}."
    except Exception as e:
        return f"Error fetching quote for {symbol}: {str(e)}" 

@mcp.tool()
async def get_stock_bars(
    symbol: str, 
    days: int = 5, 
    timeframe: str = "1Day",
    limit: Optional[int] = None,
    start: Optional[str] = None,
    end: Optional[str] = None
) -> str:
    """
    Retrieves and formats historical price bars for a stock with configurable timeframe and time range.
    
    Args:
        symbol (str): Stock ticker symbol (e.g., AAPL, MSFT)
        days (int): Number of days to look back (default: 5, ignored if start/end provided)
        timeframe (str): Bar timeframe - supports flexible Alpaca formats:
            - Minutes: "1Min", "2Min", "3Min", "4Min", "5Min", "15Min", "30Min", etc.
            - Hours: "1Hour", "2Hour", "3Hour", "4Hour", "6Hour", etc.
            - Days: "1Day", "2Day", "3Day", etc.
            - Weeks: "1Week", "2Week", etc.
            - Months: "1Month", "2Month", etc.
            (default: "1Day")
        limit (Optional[int]): Maximum number of bars to return (optional)
        start (Optional[str]): Start time in ISO format (e.g., "2023-01-01T09:30:00" or "2023-01-01")
        end (Optional[str]): End time in ISO format (e.g., "2023-01-01T16:00:00" or "2023-01-01")
    
    Returns:
        str: Formatted string containing historical price data with timestamps, OHLCV data
    """
    try:
        # Parse timeframe string to TimeFrame object
        timeframe_obj = parse_timeframe_with_enums(timeframe)
        if timeframe_obj is None:
            return f"Error: Invalid timeframe '{timeframe}'. Supported formats: 1Min, 2Min, 4Min, 5Min, 15Min, 30Min, 1Hour, 2Hour, 4Hour, 1Day, 1Week, 1Month, etc."
        
        # Parse start/end times or calculate from days
        start_time = None
        end_time = None
        
        if start:
            try:
                start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
            except ValueError:
                return f"Error: Invalid start time format '{start}'. Use ISO format like '2023-01-01T09:30:00' or '2023-01-01'"
                
        if end:
            try:
                end_time = datetime.fromisoformat(end.replace('Z', '+00:00'))
            except ValueError:
                return f"Error: Invalid end time format '{end}'. Use ISO format like '2023-01-01T16:00:00' or '2023-01-01'"

        if not start_time:
            if limit and timeframe_obj.unit_value in [TimeFrameUnit.Minute, TimeFrameUnit.Hour]:
                # Calculate based on limit and timeframe for intraday data
                if timeframe_obj.unit_value == TimeFrameUnit.Minute:
                    minutes_back = limit * timeframe_obj.amount
                    start_time = datetime.now() - timedelta(minutes=minutes_back)
                elif timeframe_obj.unit_value == TimeFrameUnit.Hour:
                    hours_back = limit * timeframe_obj.amount
                    start_time = datetime.now() - timedelta(hours=hours_back)
            else:
                # Fall back to days parameter for daily+ timeframes
                start_time = datetime.now() - timedelta(days=days)
        if not end_time:
            end_time = datetime.now()
        
        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=timeframe_obj,
            start=start_time,
            end=end_time,
            limit=limit
        )
        
        bars = stock_historical_data_client.get_stock_bars(request_params)

        if bars[symbol]:
            time_range = f"{start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}"
            result = f"Historical Data for {symbol} ({timeframe} bars, {time_range}):\n"
            result += "---------------------------------------------------\n"
            
            for bar in bars[symbol]:
                # Format timestamp based on timeframe unit
                if timeframe_obj.unit_value in [TimeFrameUnit.Minute, TimeFrameUnit.Hour]:
                    time_str = bar.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    time_str = bar.timestamp.date()
                
                result += f"Time: {time_str}, Open: ${bar.open:.2f}, High: ${bar.high:.2f}, Low: ${bar.low:.2f}, Close: ${bar.close:.2f}, Volume: {bar.volume}\n"
            
            return result
        else:
            return f"No historical data found for {symbol} with {timeframe} timeframe in the specified time range."
    except Exception as e:
        return f"Error fetching historical data for {symbol}: {str(e)}"

@mcp.tool()
async def get_stock_trades(
    symbol: str,
    days: int = 5,
    limit: Optional[int] = None,
    sort: Optional[Sort] = Sort.ASC,
    feed: Optional[DataFeed] = None,
    currency: Optional[SupportedCurrencies] = None,
    asof: Optional[str] = None
) -> str:
    """
    Retrieves and formats historical trades for a stock.
    
    Args:
        symbol (str): Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        days (int): Number of days to look back (default: 5)
        limit (Optional[int]): Upper limit of number of data points to return
        sort (Optional[Sort]): Chronological order of response (ASC or DESC)
        feed (Optional[DataFeed]): The stock data feed to retrieve from
        currency (Optional[SupportedCurrencies]): Currency for prices (default: USD)
        asof (Optional[str]): The asof date in YYYY-MM-DD format
    
    Returns:
        str: Formatted string containing trade history or an error message
    """
    try:
        # Calculate start time based on days
        start_time = datetime.now() - timedelta(days=days)
        
        # Create the request object with all available parameters
        request_params = StockTradesRequest(
            symbol_or_symbols=symbol,
            start=start_time,
            end=datetime.now(),
            limit=limit,
            sort=sort,
            feed=feed,
            currency=currency,
            asof=asof
        )
                
        trades = stock_historical_data_client.get_stock_trades(request_params)
        
        if symbol in trades:
            result = f"Historical Trades for {symbol} (Last {days} days):\n"
            result += "---------------------------------------------------\n"
            
            for trade in trades[symbol]:
                result += f"""
                    Time: {trade.timestamp}
                    Price: ${float(trade.price):.6f}
                    Size: {trade.size}
                    Exchange: {trade.exchange}
                    ID: {trade.id}
                    Conditions: {trade.conditions}
                    -------------------
                    """
            return result
        else:
            return f"No trade data found for {symbol} in the last {days} days."
    except Exception as e:
        return f"Error fetching trades: {str(e)}"

@mcp.tool()
async def get_stock_latest_trade(
    symbol: str,
    feed: Optional[DataFeed] = None,
    currency: Optional[SupportedCurrencies] = None
) -> str:
    """Get the latest trade for a stock.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        feed: The stock data feed to retrieve from (optional)
        currency: The currency for prices (optional, defaults to USD)
    
    Returns:
        A formatted string containing the latest trade details or an error message
    """
    try:
        # Create the request object with all available parameters
        request_params = StockLatestTradeRequest(
            symbol_or_symbols=symbol,
            feed=feed,
            currency=currency
        )
        
        latest_trades = stock_historical_data_client.get_stock_latest_trade(request_params)
        
        if symbol in latest_trades:
            trade = latest_trades[symbol]
            return f"""
                Latest Trade for {symbol}:
                ---------------------------
                Time: {trade.timestamp}
                Price: ${float(trade.price):.6f}
                Size: {trade.size}
                Exchange: {trade.exchange}
                ID: {trade.id}
                Conditions: {trade.conditions}
                """
        else:
            return f"No latest trade data found for {symbol}."
    except Exception as e:
        return f"Error fetching latest trade: {str(e)}"
        
@mcp.tool()
async def get_stock_latest_bar(
    symbol: str,
    feed: Optional[DataFeed] = None,
    currency: Optional[SupportedCurrencies] = None
) -> str:
    """Get the latest minute bar for a stock.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        feed: The stock data feed to retrieve from (optional)
        currency: The currency for prices (optional, defaults to USD)
    
    Returns:
        A formatted string containing the latest bar details or an error message
    """
    try:
        # Create the request object with all available parameters
        request_params = StockLatestBarRequest(
            symbol_or_symbols=symbol,
            feed=feed,
            currency=currency
        )
        
        # Get the latest bar
        latest_bars = stock_historical_data_client.get_stock_latest_bar(request_params)
        
        if symbol in latest_bars:
            bar = latest_bars[symbol]
            return f"""
                Latest Minute Bar for {symbol}:
                ---------------------------
                Time: {bar.timestamp}
                Open: ${float(bar.open):.2f}
                High: ${float(bar.high):.2f}
                Low: ${float(bar.low):.2f}
                Close: ${float(bar.close):.2f}
                Volume: {bar.volume}
                """
        else:
            return f"No latest bar data found for {symbol}."
    except Exception as e:
        return f"Error fetching latest bar: {str(e)}"

# ============================================================================
# Market Data Tools - Stock Snapshot Data with Helper Functions
# ============================================================================

def _format_ohlcv_bar(bar, bar_type: str, include_time: bool = True) -> str:
    """Helper function to format OHLCV bar data consistently."""
    if not bar:
        return ""
    
    time_format = '%Y-%m-%d %H:%M:%S %Z' if include_time else '%Y-%m-%d'
    time_label = "Timestamp" if include_time else "Date"
    
    return f"""{bar_type}:
  Open: ${bar.open:.2f}, High: ${bar.high:.2f}, Low: ${bar.low:.2f}, Close: ${bar.close:.2f}
  Volume: {bar.volume:,}, {time_label}: {bar.timestamp.strftime(time_format)}
  """

def _format_quote_data(quote) -> str:
    """Helper function to format quote data consistently."""
    if not quote:
        return ""
    
    return f"""Latest Quote:
  Bid: ${quote.bid_price:.2f} x {quote.bid_size}, Ask: ${quote.ask_price:.2f} x {quote.ask_size}
  Timestamp: {quote.timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}

"""


def _format_trade_data(trade) -> str:
    """Helper function to format trade data consistently."""
    if not trade:
        return ""
    
    optional_fields = []
    if hasattr(trade, 'exchange') and trade.exchange:
        optional_fields.append(f"Exchange: {trade.exchange}")
    if hasattr(trade, 'conditions') and trade.conditions:
        optional_fields.append(f"Conditions: {trade.conditions}")
    if hasattr(trade, 'id') and trade.id:
        optional_fields.append(f"ID: {trade.id}")
    
    optional_str = f", {', '.join(optional_fields)}" if optional_fields else ""
    
    return f"""Latest Trade:
  Price: ${trade.price:.2f}, Size: {trade.size}{optional_str}
  Timestamp: {trade.timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}

"""

@mcp.tool()
async def get_stock_snapshot(
    symbol_or_symbols: Union[str, List[str]], 
    feed: Optional[DataFeed] = None,
    currency: Optional[SupportedCurrencies] = None
) -> str:
    """
    Retrieves comprehensive snapshots of stock symbols including latest trade, quote, minute bar, daily bar, and previous daily bar.
    
    Args:
        symbol_or_symbols: Single stock symbol or list of stock symbols (e.g., 'AAPL' or ['AAPL', 'MSFT'])
        feed: The stock data feed to retrieve from (optional)
        currency: The currency the data should be returned in (default: USD)
    
    Returns:
        Formatted string with comprehensive snapshots including:
        - latest_quote: Current bid/ask prices and sizes
        - latest_trade: Most recent trade price, size, and exchange
        - minute_bar: Latest minute OHLCV bar
        - daily_bar: Current day's OHLCV bar  
        - previous_daily_bar: Previous trading day's OHLCV bar
    """

    
