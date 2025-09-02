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
