import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, date
import plotly.graph_objs as go
import json
from decimal import Decimal
import locale
import os
import boto3
from botocore.exceptions import ClientError

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
                # Try direct symbol search first - handle common tickers
                # Map for common company names to their symbols
                common_companies = {
                    'nvidia': 'NVDA',
                    'apple': 'AAPL',
                    'microsoft': 'MSFT',
                    'amazon': 'AMZN',
                    'google': 'GOOGL',
                    'alphabet': 'GOOGL',
                    'tesla': 'TSLA',
                    'meta': 'META',
                    'facebook': 'META',
                    'netflix': 'NFLX',
                    'berkshire': 'BRK-B',
                    'berkshire hathaway': 'BRK-B',
                    'jpmorgan': 'JPM',
                    'j.p. morgan': 'JPM',
                    'coca cola': 'KO',
                    'coca-cola': 'KO',
                    'disney': 'DIS',
                    'walmart': 'WMT',
                    'johnson & johnson': 'JNJ',
                    'johnson and johnson': 'JNJ',
                    'visa': 'V',
                    'mastercard': 'MA',
                    'intel': 'INTC',
                    'amd': 'AMD',
                    'qualcomm': 'QCOM',
                    'ibm': 'IBM'
                }
                
                # Check if name matches any common company
                name_lower = name.lower()
                for company_name, symbol in common_companies.items():
                    if company_name in name_lower or name_lower in company_name:
                        try:
                            stock = yf.Ticker(symbol)
                            stock_info = stock.info
                            if stock_info and ('shortName' in stock_info or 'longName' in stock_info):
                                stock_name = stock_info.get('shortName', '') or stock_info.get('longName', '')
                                return [{
                                    'symbol': symbol,
                                    'name': stock_name
                                }]
                        except Exception as e:
                            print(f"Error checking common company {company_name} ({symbol}): {e}")
                            continue
            
                # Try direct ticker search as a fallback  
                try:
                    stock = yf.Ticker(name.upper())
                    stock_info = stock.info
                    # Check if stock_info is None or empty (which can happen with 404 errors)
                    if not stock_info:
                        print(f"No data found for ticker {name.upper()} - API returned empty response")
                        # Continue to other search methods instead of failing
                    elif ('shortName' in stock_info or 'longName' in stock_info):
                        stock_name = stock_info.get('shortName', '') or stock_info.get('longName', '')
                        return [{
                            'symbol': name.upper(),
                            'name': stock_name
                        }]
                except Exception as e:
                    print(f"Error with direct ticker search for {name}: {e}")
                    # Continue to other search methods instead of failing
                    
                # Try to load the ticker lists with yahoo_fin
                try:
                    import yahoo_fin.stock_info as stock_info
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
                            stock_info = stock.info
                            if stock_info and ('shortName' in stock_info or 'longName' in stock_info):
                                stock_name = stock_info.get('shortName', '') or stock_info.get('longName', '')
                                if name_lower in stock_name.lower():
                                    potential_matches.append({
                                        'symbol': ticker,
                                        'name': stock_name
                                    })
                        except Exception:
                            continue
                    
                    if potential_matches:
                        return potential_matches
                except Exception as e:
                    print(f"Error with ticker list search: {e}")
                    
                # Last resort: Try the simple direct approach
                try:
                    print(f"Trying direct search for ticker '{name}'")
                    stock = yf.Ticker(name)
                    stock_info = stock.info
                    # Check if stock_info is None or empty (which can happen with 404 errors)
                    if not stock_info:
                        print(f"No data found for ticker {name} - API returned empty response")
                        # Return helpful message instead of empty results
                        return [{
                            'symbol': name,
                            'name': "No data found for this ticker. Try a different search term."
                        }]
                    elif ('shortName' in stock_info or 'longName' in stock_info):
                        stock_name = stock_info.get('shortName', '') or stock_info.get('longName', '')
                        return [{
                            'symbol': name,
                            'name': stock_name
                        }]
                except Exception as e:
                    print(f"Error with final direct search: {e}")
                    # Return helpful message instead of empty results
                    return [{
                        'symbol': name,
                        'name': "Error retrieving data. Try a different search term."
                    }]
                        
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
            
            # Check if info is None (which can happen with 404 errors)
            if not info:
                print(f"No data found for symbol {query_symbol} - API returned empty response")
                return None
                
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
            
            # Get stock name
            name = info.get('shortName', info.get('longName', symbol))
            
            # Get Chinese name for HK/CN stocks if available
            chinese_name = None
            if market in ['HK', 'CN']:
                # This is a placeholder implementation
                # In a real-world scenario, you would use a database or API to look up Chinese names
                # Some common examples for demonstration:
                common_stocks = {
                    # HK stocks
                    '0700': '腾讯控股',
                    '9988': '阿里巴巴',
                    '0941': '中国移动',
                    '0005': '汇丰控股',
                    '3690': '美团',
                    # CN stocks
                    '600519': '贵州茅台',
                    '601398': '工商银行',
                    '600036': '招商银行',
                    '601318': '中国平安',
                    '000858': '五粮液',
                }
                chinese_name = common_stocks.get(symbol)
            
            # Get basic data
            stock_data = {
                'symbol': symbol,
                'name': name,
                'chinese_name': chinese_name,
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
    def format_currency(value, market='US'):
        """Format currency values based on market"""
        if value is None:
            return None
            
        try:
            value = float(value)
            if market == 'HK':
                prefix = 'HK$'
            elif market == 'CN':
                prefix = '¥'
            else:
                prefix = '$'
                
            # Format large numbers for readability
            if abs(value) >= 1e9:
                return f"{prefix}{value/1e9:.2f}B"
            elif abs(value) >= 1e6:
                return f"{prefix}{value/1e6:.2f}M"
            elif abs(value) >= 1e3:
                return f"{prefix}{value/1e3:.2f}K"
            else:
                return f"{prefix}{value:.2f}"
        except:
            return str(value)
    
    @staticmethod
    def get_balance_sheet_data(symbol, market='US'):
        """
        Get the latest quarterly balance sheet data
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
            
            # Get quarterly balance sheet (most recent first)
            balance_sheet = stock.quarterly_balance_sheet
            
            if balance_sheet is None or balance_sheet.empty:
                print(f"No balance sheet data available for {query_symbol}")
                return None
                
            # Get the most recent quarter's data (first column)
            latest_quarter = balance_sheet.columns[0]
            latest_data = balance_sheet[latest_quarter]
            
            # Convert to dictionary
            balance_sheet_data = {
                'quarter_date': latest_quarter.strftime('%Y-%m-%d'),
                'total_assets': float(latest_data.get('Total Assets', 0)),
                'total_liabilities': float(latest_data.get('Total Liabilities Net Minority Interest', 0)),
                'equity': float(latest_data.get('Total Equity Gross Minority Interest', 0)),
                'cash': float(latest_data.get('Cash And Cash Equivalents', 0)),
                'debt': float(latest_data.get('Total Debt', 0)),
                'current_assets': float(latest_data.get('Total Current Assets', 0)),
                'current_liabilities': float(latest_data.get('Total Current Liabilities', 0)),
                'inventory': float(latest_data.get('Inventory', 0)),
                'accounts_receivable': float(latest_data.get('Accounts Receivable', 0)),
                'accounts_payable': float(latest_data.get('Accounts Payable', 0)),
            }
            
            # Calculate some additional ratios
            try:
                # Current ratio
                if balance_sheet_data['current_liabilities'] != 0:
                    balance_sheet_data['current_ratio'] = balance_sheet_data['current_assets'] / balance_sheet_data['current_liabilities']
                else:
                    balance_sheet_data['current_ratio'] = None
                    
                # Debt to equity ratio
                if balance_sheet_data['equity'] != 0:
                    balance_sheet_data['debt_equity_ratio'] = balance_sheet_data['debt'] / balance_sheet_data['equity']
                else:
                    balance_sheet_data['debt_equity_ratio'] = None
                    
                # Cash ratio
                if balance_sheet_data['current_liabilities'] != 0:
                    balance_sheet_data['cash_ratio'] = balance_sheet_data['cash'] / balance_sheet_data['current_liabilities']
                else:
                    balance_sheet_data['cash_ratio'] = None
            except Exception as e:
                print(f"Error calculating balance sheet ratios: {e}")
                
            return balance_sheet_data
            
        except Exception as e:
            print(f"Error fetching balance sheet data for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return None

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
            
    @staticmethod
    def get_stock_insights(user_message):
        """
        Generate responses to user messages using LLM via Amazon Bedrock
        
        Args:
            user_message (str): User's message to the chatbot
            
        Returns:
            str: Response from the LLM
        """
        try:
            # Create the prompt for the LLM (simple conversational context)
            prompt = f"""You are a helpful assistant focused on financial topics and markets. Your name is ValueBot.

The user has asked: "{user_message}"

Use the language which the user input, and provide a helpful, accurate, and concise response.
If you don't have specific information to answer the question, acknowledge that limitation.
Format your response with clean line breaks and bullet points where appropriate.
"""
            
            # Check if we should use mock responses for testing
            if os.getenv('USE_MOCK_LLM', 'false').lower() == 'true':
                # Simple mock response for testing
                return f"This is a mock response to: {user_message}"
            
            # Otherwise use Amazon Bedrock API
            return StockService._call_bedrock_llm(prompt)
                
        except Exception as e:
            print(f"Error in get_stock_insights: {e}")
            import traceback
            traceback.print_exc()
            return "Sorry, I encountered an error while processing your request."
            
    @staticmethod
    def _call_bedrock_llm(prompt):
        """
        Call Amazon Bedrock API to get LLM response
        """
        try:
            # Initialize the Bedrock client
            bedrock_runtime = boto3.client(
                service_name='bedrock-runtime',
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
            
            # Define the model parameters
            # Use Claude 3.5 Sonnet as default
            model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-7-sonnet-20250219-v1:0')
            
            # Prepare the request body for Claude models
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4000,
                "top_k": 250,
                "stop_sequences": [],
                "temperature": 1,
                "top_p": 0.999,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            # Make the API call
            response = bedrock_runtime.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body)
            )
            
            # Parse the response for Claude models
            response_body = json.loads(response.get('body').read())
            
            # Extract the response text from the Claude response format
            return response_body.get('content', [{}])[0].get('text', "No response generated")
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            error_message = e.response.get("Error", {}).get("Message")
            print(f"Bedrock API error: {error_code} - {error_message}")
            
            # Return a graceful fallback response
            return "I'm having trouble accessing the AI service right now. Please try again later."
        except Exception as e:
            print(f"Error calling Bedrock LLM: {e}")
            import traceback
            traceback.print_exc()
            
            # Return a graceful fallback response
            return "I'm having trouble generating a response right now. Please try again later."
    
    @staticmethod
    def _get_mock_insight_response(stock_data, balance_sheet, user_message):
        """
        Generate mock LLM responses for testing without API calls
        """
        # Mock response for demonstration or testing
        if "dividend" in user_message.lower():
            name = stock_data.get('name', 'this stock')
            if stock_data.get('dividend_yield') is not None:
                yield_value = f"{stock_data.get('dividend_yield', 0) * 100:.2f}%"
                return f"The current dividend yield for {name} is {yield_value}."
            else:
                return f"{name} doesn't currently pay dividends."
        
        elif "pe ratio" in user_message.lower() or "p/e" in user_message.lower():
            name = stock_data.get('name', 'this stock')
            if stock_data.get('pe_ratio') is not None:
                return f"The P/E ratio for {name} is {stock_data.get('pe_ratio'):.2f}."
            else:
                return f"I couldn't find P/E ratio data for {name}."
        
        elif "competitors" in user_message.lower():
            # This would normally use industry data to provide competitors
            name = stock_data.get('name', 'this stock')
            return f"As a finance assistant, I could analyze competitors of {name}, but that would require more comprehensive industry data."
        
        elif "balance sheet" in user_message.lower():
            if balance_sheet:
                # Check if each value exists before formatting
                assets = f"${balance_sheet.get('total_assets')/1e9:.2f}B" if balance_sheet.get('total_assets') is not None else "N/A"
                liabilities = f"${balance_sheet.get('total_liabilities')/1e9:.2f}B" if balance_sheet.get('total_liabilities') is not None else "N/A"
                equity = f"${balance_sheet.get('equity')/1e9:.2f}B" if balance_sheet.get('equity') is not None else "N/A"
                debt_equity = f"{balance_sheet.get('debt_equity_ratio'):.2f}" if balance_sheet.get('debt_equity_ratio') is not None else "N/A"
                
                return (
                    f"Based on the latest balance sheet for {stock_data.get('name')}:\n"
                    f"• Total Assets: {assets}\n"
                    f"• Total Liabilities: {liabilities}\n"
                    f"• Equity: {equity}\n"
                    f"• Debt to Equity Ratio: {debt_equity}"
                )
            else:
                return f"I don't have balance sheet data available for {stock_data.get('name')}."
        
        else:
            # General response for other queries
            name = stock_data.get('name', 'this stock')
            symbol = stock_data.get('symbol', '')
            
            # Format price and market cap safely
            if stock_data.get('current_price') is not None:
                price = f"${stock_data.get('current_price'):.2f}"
            else:
                price = "N/A"
                
            if stock_data.get('market_cap') is not None:
                market_cap = f"${stock_data.get('market_cap')/1e9:.2f}B"
            else:
                market_cap = "N/A"
                
            return (
                f"I can provide insights about {name} ({symbol}).\n\n"
                f"The current stock price is {price} with a market cap of {market_cap}.\n\n"
                f"You can ask me about the company's financials, performance, valuation, or specific metrics like P/E ratio, dividend yield, etc."
            )