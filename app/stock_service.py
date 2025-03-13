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
    def get_historical_data(symbol, market='US', period='5y'):
        """
        Get historical price data, default to 5 years
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
    def get_index_data(market='US', period='5y'):
        """
        Get historical price data for market index:
        - US: S&P 500 (^GSPC)
        - HK: Hang Seng Index (^HSI)
        - CN: CSI 300 (000300.SS)
        """
        try:
            index_ticker = "^GSPC"  # S&P 500 default
            index_name = "S&P 500"
            
            if market == 'HK':
                index_ticker = "^HSI"  # Hang Seng Index
                index_name = "Hang Seng Index"
            elif market == 'CN':
                index_ticker = "000300.SS"  # CSI 300 Index
                index_name = "CSI 300"
                
            print(f"Fetching {index_name} historical data for {period}")
            index_data = yf.Ticker(index_ticker).history(period=period)
            
            if index_data is None or index_data.empty:
                print(f"No {index_name} historical data returned")
                return None, index_name
                
            print(f"Retrieved {len(index_data)} {index_name} historical data points")
            return index_data, index_name
        except Exception as e:
            print(f"Error fetching {market} index data: {e}")
            return None, "Market Index"
    
    @staticmethod
    def generate_chart(stock_data, market='US', stock_symbol=None):
        """
        Generate interactive chart data for the stock price history
        Shows 5-year actual price history of the stock
        """
        if stock_data is None or stock_data.empty:
            print("Cannot generate chart: stock_data is None or empty")
            return None
            
        try:
            print("Generating chart from historical data")
            
            # Verify we have the required columns
            if 'Close' not in stock_data.columns:
                print("Missing required 'Close' column in stock data")
                return None
            
            # Print some details about the data for debugging
            print(f"Stock data date range: {stock_data.index.min()} to {stock_data.index.max()}")
            
            # Create figure
            fig = go.Figure()
            
            # Use provided stock_symbol if available
            display_symbol = stock_symbol if stock_symbol else "Stock"
            
            # Add stock price line - actual price, not normalized
            fig.add_trace(go.Scatter(
                x=stock_data.index,
                y=stock_data['Close'],
                name=display_symbol,
                line=dict(color='rgb(0, 100, 255)', width=3),
                mode='lines',
                hovertemplate='$%{y:.2f}'
            ))
            
            # Add candlestick view for more detailed price information
            fig.add_trace(go.Candlestick(
                x=stock_data.index,
                open=stock_data['Open'],
                high=stock_data['High'],
                low=stock_data['Low'],
                close=stock_data['Close'],
                name="OHLC",
                visible='legendonly'  # Hidden by default, can be enabled from legend
            ))
            
            # Layout settings
            fig.update_layout(
                title=f'5-Year Price History: {display_symbol}',
                yaxis=dict(
                    title='Price (USD)',
                    tickformat='.2f',
                    hoverformat='.2f',
                    showgrid=True,
                    zeroline=True,
                    zerolinecolor='black',
                    autorange=True
                ),
                xaxis=dict(
                    title='Date (2019-2024)',
                    rangeslider=dict(visible=False)
                ),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
                height=600,
                hovermode='x unified'
            )
            
            chart_json = fig.to_json()
            print(f"Chart JSON generated successfully (length: {len(chart_json)})")
            return chart_json
            
        except Exception as e:
            print(f"Error generating chart: {e}")
            import traceback
            traceback.print_exc()
            return None