import yfinance as yf
import pandas as pd
import requests
from datetime import datetime
import plotly.graph_objs as go
import json

class StockService:
    @staticmethod
    def get_stock_data(symbol, market='US'):
        """
        Get stock data based on symbol and market
        Market can be: US, HK, CN (China Mainland)
        """
        try:
            # Adjust the symbol based on market
            if market == 'HK':
                query_symbol = f"{symbol}.HK"
            elif market == 'CN':
                query_symbol = f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ"
            else:  # US market
                query_symbol = symbol
                
            stock = yf.Ticker(query_symbol)
            info = stock.info
            
            # Get basic data
            stock_data = {
                'symbol': symbol,
                'name': info.get('shortName', info.get('longName', symbol)),
                'current_price': info.get('currentPrice', info.get('regularMarketPrice')),
                'change_percent': info.get('regularMarketChangePercent'),
                'market_cap': info.get('marketCap'),
                'volume': info.get('volume'),
                'pe_ratio': info.get('trailingPE'),
                'eps': info.get('trailingEps'),
                'dividend_yield': info.get('dividendYield'),
                '52_week_high': info.get('fiftyTwoWeekHigh'),
                '52_week_low': info.get('fiftyTwoWeekLow'),
            }
            
            return stock_data
            
        except Exception as e:
            print(f"Error fetching stock data for {symbol}: {e}")
            return None

    @staticmethod
    def get_historical_data(symbol, market='US', period='1y'):
        """
        Get historical price data
        """
        try:
            # Adjust the symbol based on market
            if market == 'HK':
                query_symbol = f"{symbol}.HK"
            elif market == 'CN':
                query_symbol = f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ"
            else:  # US market
                query_symbol = symbol
                
            print(f"Fetching historical data for {query_symbol} ({period})")
            hist_data = yf.Ticker(query_symbol).history(period=period)
            
            if hist_data is None or hist_data.empty:
                print(f"No historical data returned for {query_symbol}")
                return None
                
            print(f"Retrieved {len(hist_data)} historical data points for {query_symbol}")
            print(f"Columns available: {list(hist_data.columns)}")
            print(f"Date range: {hist_data.index.min()} to {hist_data.index.max()}")
            
            return hist_data
        except Exception as e:
            print(f"Error fetching historical data for {symbol} ({query_symbol}): {e}")
            return None
            
    @staticmethod
    def generate_chart(stock_data):
        """
        Generate interactive chart data for the stock
        """
        if stock_data is None or stock_data.empty:
            print("Cannot generate chart: stock_data is None or empty")
            return None
            
        try:
            print("Generating chart from historical data")
            
            # Verify we have the required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_columns:
                if col not in stock_data.columns:
                    print(f"Missing required column: {col}")
                    return None
                
            fig = go.Figure()
            
            # Add candlestick chart
            fig.add_trace(go.Candlestick(
                x=stock_data.index,
                open=stock_data['Open'],
                high=stock_data['High'],
                low=stock_data['Low'],
                close=stock_data['Close'],
                name='Price'
            ))
            
            # Add volume bars
            fig.add_trace(go.Bar(
                x=stock_data.index,
                y=stock_data['Volume'],
                name='Volume',
                yaxis='y2'
            ))
            
            # Layout settings
            fig.update_layout(
                title='Stock Price & Volume',
                yaxis_title='Price',
                yaxis2=dict(
                    title='Volume',
                    overlaying='y',
                    side='right',
                    showgrid=False
                ),
                xaxis_rangeslider_visible=False,
                height=600
            )
            
            chart_json = fig.to_json()
            print(f"Chart JSON generated successfully (length: {len(chart_json)})")
            return chart_json
            
        except Exception as e:
            print(f"Error generating chart: {e}")
            import traceback
            traceback.print_exc()
            return None