import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, date
import plotly.graph_objs as go
import json

class StockService:
    @staticmethod
    def search_by_name(name, market='US'):
        """
        Search for stocks by company name in a specific market
        Returns a list of potential matches with symbol and name
        """
        try:
            # Use yfinance to search by name
            # This is a basic implementation - in production you might want to use a more robust API
            results = []
            
            # Perform search based on the market
            if market == 'US':
                # For US stocks, search on NASDAQ and NYSE
                from yahoo_fin import stock_info
                try:
                    nasdaq_list = stock_info.tickers_nasdaq()
                    nyse_list = stock_info.tickers_other()
                    
                    # Combine both exchanges
                    all_tickers = nasdaq_list + nyse_list
                    
                    # Filter by name (case-insensitive)
                    name_lower = name.lower()
                    potential_matches = []
                    
                    # First pass: Get info for several potential matches
                    for ticker in all_tickers[:1000]:  # Limit to avoid too many API calls
                        if len(potential_matches) >= 10:
                            break
                            
                        try:
                            stock = yf.Ticker(ticker)
                            stock_name = stock.info.get('shortName', '') or stock.info.get('longName', '')
                            if name_lower in stock_name.lower():
                                potential_matches.append({
                                    'symbol': ticker,
                                    'name': stock_name
                                })
                        except:
                            continue
                    
                    # Return the matches
                    return potential_matches
                    
                except Exception as e:
                    print(f"Error searching US stocks: {e}")
                    
                    # Fallback method using direct Yahoo Finance
                    try:
                        # Try a more direct search using yfinance's search capabilities
                        # This is limited but can provide some results
                        stock = yf.Ticker(name)
                        stock_name = stock.info.get('shortName', None) or stock.info.get('longName', None)
                        if stock_name:
                            return [{
                                'symbol': stock.ticker,
                                'name': stock_name
                            }]
                    except:
                        pass
                        
            # For other markets, provide a simplified search based on common patterns
            elif market == 'HK':
                # Return some helpful guidance for HK stocks
                return [{
                    'symbol': 'Please use the ticker directly',
                    'name': 'For HK stocks, use the numeric code (e.g. 0700 for Tencent)'
                }]
            elif market == 'CN':
                # Return some helpful guidance for China stocks
                return [{
                    'symbol': 'Please use the ticker directly',
                    'name': 'For China A-shares, use the numeric code (e.g. 600519 for Kweichow Moutai)'
                }]
                
            return results
            
        except Exception as e:
            print(f"Error searching stocks by name: {e}")
            return []

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
            
            # Get earnings per share (EPS) from trailing 12 months
            eps = info.get('trailingEps')
            
            # Calculate ROI (EPS/Price) as percentage
            prospect_return = None
            current_price = info.get('currentPrice', info.get('regularMarketPrice'))
            if eps is not None and current_price is not None and current_price > 0:
                prospect_return = (eps / current_price) * 100
                
            # Get Return on Equity (ROE) from last fiscal year
            roe = None
            try:
                roe = info.get('returnOnEquity')
                if roe is not None:
                    # Convert from decimal to percentage
                    roe = roe * 100
            except Exception as e:
                print(f"Error fetching ROE for {symbol}: {e}")
            
            # Get basic data
            stock_data = {
                'symbol': symbol,
                'name': info.get('shortName', info.get('longName', symbol)),
                'current_price': current_price,
                'change_percent': info.get('regularMarketChangePercent'),
                'ytd_change_percent': None,  # Setting to None as per request
                'eps': eps,
                'prospect_return': prospect_return,  # ROI
                'roe': roe,
                'market_cap': info.get('marketCap'),
                'volume': info.get('volume'),
                'pe_ratio': info.get('trailingPE'),
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