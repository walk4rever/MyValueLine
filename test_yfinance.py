#!/usr/bin/env python3
"""
Test script for yfinance functionality to confirm it's working correctly
"""

import yfinance as yf
import pandas as pd
import json
from datetime import datetime

def test_stock_data(symbol='AAPL', market='US'):
    """Test retrieving current stock data"""
    print(f"\n=== Testing current stock data for {symbol} ({market}) ===")
    
    # Adjust the symbol based on market
    if market == 'HK':
        query_symbol = f"{symbol}.HK"
    elif market == 'CN':
        query_symbol = f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ"
    else:  # US market
        query_symbol = symbol
    
    try:
        print(f"Querying stock data for {query_symbol}")
        stock = yf.Ticker(query_symbol)
        info = stock.info
        
        # Print some basic data
        print(f"Info dict contains {len(info)} items")
        print(f"Stock name: {info.get('shortName', info.get('longName', 'N/A'))}")
        print(f"Current price: {info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))}")
        print(f"Currency: {info.get('currency', 'N/A')}")
        return True
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return False
        
def test_historical_data(symbol='AAPL', market='US', period='1y'):
    """Test retrieving historical data"""
    print(f"\n=== Testing historical data for {symbol} ({market}) for period {period} ===")
    
    # Adjust the symbol based on market
    if market == 'HK':
        query_symbol = f"{symbol}.HK"
    elif market == 'CN':
        query_symbol = f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ"
    else:  # US market
        query_symbol = symbol
    
    try:
        print(f"Querying historical data for {query_symbol}")
        hist_data = yf.Ticker(query_symbol).history(period=period)
        
        if hist_data is None or hist_data.empty:
            print("No historical data returned!")
            return False
        
        print(f"Retrieved {len(hist_data)} historical data points")
        print(f"Columns: {list(hist_data.columns)}")
        print(f"Date range: {hist_data.index.min()} to {hist_data.index.max()}")
        
        # Print first few rows
        print("\nFirst 3 rows of data:")
        print(hist_data.head(3))
        
        return True
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return False

if __name__ == "__main__":
    # Test US stock
    test_stock_data('AAPL', 'US')
    test_historical_data('AAPL', 'US', '1y')
    
    # Test alternate period
    test_historical_data('AAPL', 'US', '1mo')
    
    # Uncomment to test Hong Kong stock
    # test_stock_data('0700', 'HK')  
    # test_historical_data('0700', 'HK')
    
    # Uncomment to test China A share
    # test_stock_data('600000', 'CN')
    # test_historical_data('600000', 'CN')