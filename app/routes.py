from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from app.models import Stock
from app.stock_service import StockService
from datetime import datetime, date
import json

@app.route('/')
def index():
    """Display the portfolio dashboard"""
    stocks = Stock.query.order_by(Stock.display_order).all()
    
    # Update latest prices for all stocks
    for stock in stocks:
        try:
            # Only update if it's been a while since last update
            if not stock.last_updated or (datetime.utcnow() - stock.last_updated).seconds > 3600:
                data = StockService.get_stock_data(stock.symbol, stock.market)
                if data and 'current_price' in data:
                    stock.current_price = data['current_price']
                    stock.change_percent = data.get('change_percent', 0)
                    stock.ytd_change_percent = data.get('ytd_change_percent')
                    stock.eps = data.get('eps')
                    stock.prospect_return = data.get('prospect_return')  # ROI
                    stock.roe = data.get('roe')
                        
                    stock.last_updated = datetime.utcnow()
                    db.session.commit()
        except Exception as e:
            print(f"Failed to update {stock.symbol}: {e}")
    
    return render_template('index.html', stocks=stocks)

@app.route('/add_stock', methods=['GET', 'POST'])
def add_stock():
    """Add a new stock to the portfolio"""
    if request.method == 'POST':
        symbol = request.form.get('symbol', '').strip().upper()
        market = request.form.get('market', 'US')
        
        # Check if stock already exists
        existing_stock = Stock.query.filter_by(symbol=symbol, market=market).first()
        if existing_stock:
            flash(f'Stock {symbol} already exists in your portfolio!')
            return redirect(url_for('index'))
        
        # Get stock data
        stock_data = StockService.get_stock_data(symbol, market)
        
        if not stock_data or 'current_price' not in stock_data or not stock_data['current_price']:
            flash(f'Could not find valid stock data for {symbol}. Please ensure the stock symbol exists.')
            return render_template('add_stock.html')
        
        # Create new stock
        new_stock = Stock(
            symbol=symbol,
            name=stock_data.get('name', symbol),
            chinese_name=stock_data.get('chinese_name'),
            market=market,
            current_price=stock_data.get('current_price'),
            change_percent=stock_data.get('change_percent'),
            ytd_change_percent=stock_data.get('ytd_change_percent'),
            eps=stock_data.get('eps'),
            prospect_return=stock_data.get('prospect_return'),  # ROI
            roe=stock_data.get('roe'),
            last_updated=datetime.utcnow()
        )
        
        db.session.add(new_stock)
        db.session.commit()
        
        flash(f'Successfully added {symbol} to your portfolio!')
        return redirect(url_for('index'))
    
    return render_template('add_stock.html')

@app.route('/stock/<int:stock_id>')
def stock_detail(stock_id):
    """Display detailed information for a specific stock"""
    stock = Stock.query.get_or_404(stock_id)
    
    # Get latest data
    stock_data = StockService.get_stock_data(stock.symbol, stock.market)
    
    # Get balance sheet data
    try:
        balance_sheet_data = StockService.get_balance_sheet_data(stock.symbol, stock.market)
        if balance_sheet_data:
            print(f"Balance sheet data retrieved for {stock.symbol}")
        else:
            print(f"No balance sheet data available for {stock.symbol}")
    except Exception as e:
        print(f"Error fetching balance sheet data for {stock.symbol}: {e}")
        balance_sheet_data = None
    
    # Get historical data for charts (5-year history)
    try:
        hist_data = StockService.get_historical_data(stock.symbol, stock.market, period='5y')
        print(f"Historical data for {stock.symbol}: {type(hist_data)} with {len(hist_data) if hist_data is not None else 0} rows")
        
        # Determine index name based on market
        index_name = "S&P 500"
        if stock.market == "HK":
            index_name = "Hang Seng Index"
        elif stock.market == "CN":
            index_name = "CSI 300"
            
        # Pass stock symbol to the chart generation function
        chart_data = StockService.generate_chart(hist_data, stock.market, stock_symbol=stock.symbol) if hist_data is not None and not hist_data.empty else None
        print(f"Chart data generated: {'Yes' if chart_data else 'No'}")
    except Exception as e:
        print(f"Error generating chart for {stock.symbol}: {e}")
        hist_data = None
        chart_data = None
        index_name = "Market Index"
    
    return render_template('stock_detail.html', 
                          stock=stock, 
                          stock_data=stock_data,
                          balance_sheet_data=balance_sheet_data,
                          chart_data=chart_data,
                          index_name=index_name)

@app.route('/delete_stock/<int:stock_id>', methods=['POST'])
def delete_stock(stock_id):
    """Remove a stock from the portfolio"""
    stock = Stock.query.get_or_404(stock_id)
    db.session.delete(stock)
    db.session.commit()
    
    flash(f'Removed {stock.symbol} from your portfolio.')
    return redirect(url_for('index'))

@app.route('/search_stock', methods=['POST'])
def search_stock():
    """API to search for a stock symbol and get data"""
    symbol = request.form.get('symbol', '').strip().upper()
    market = request.form.get('market', 'US')
    
    data = StockService.get_stock_data(symbol, market)
    
    if not data:
        return jsonify({'error': 'Stock not found'})
    
    return jsonify(data)
    
@app.route('/search_by_name', methods=['POST'])
def search_by_name():
    """API to search for stocks by company name"""
    name = request.form.get('name', '').strip()
    market = request.form.get('market', 'US')
    
    if not name or len(name) < 2:
        return jsonify({'error': 'Please enter at least 2 characters for the company name'})
    
    results = StockService.search_by_name(name, market)
    
    if not results:
        return jsonify({'error': 'No matches found'})
    
    return jsonify({'matches': results})
    
@app.route('/move_stock/<int:stock_id>/<direction>', methods=['POST'])
def move_stock(stock_id, direction):
    """Move a stock up or down in the display order"""
    if direction not in ['up', 'down']:
        flash('Invalid direction')
        return redirect(url_for('index'))
        
    stock = Stock.query.get_or_404(stock_id)
    stocks = Stock.query.order_by(Stock.display_order).all()
    
    # Find the current index of the stock
    current_index = next((i for i, s in enumerate(stocks) if s.id == stock_id), None)
    if current_index is None:
        flash('Stock not found')
        return redirect(url_for('index'))
        
    # Calculate new position
    if direction == 'up' and current_index > 0:
        # Swap with the stock above
        prev_stock = stocks[current_index - 1]
        temp_order = stock.display_order
        stock.display_order = prev_stock.display_order
        prev_stock.display_order = temp_order
    elif direction == 'down' and current_index < len(stocks) - 1:
        # Swap with the stock below
        next_stock = stocks[current_index + 1]
        temp_order = stock.display_order
        stock.display_order = next_stock.display_order
        next_stock.display_order = temp_order
    
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/get_latest_stock_data/<int:stock_id>')
def get_latest_stock_data(stock_id):
    """API endpoint to get the latest stock data for auto-refresh"""
    stock = Stock.query.get_or_404(stock_id)
    
    # Get latest data
    stock_data = StockService.get_stock_data(stock.symbol, stock.market)
    
    if not stock_data:
        return jsonify({'error': 'Could not fetch latest data'}), 404
    
    return jsonify(stock_data)

@app.route('/get_all_stocks_data')
def get_all_stocks_data():
    """API endpoint to get latest data for all stocks in portfolio"""
    stocks = Stock.query.order_by(Stock.display_order).all()
    result = {}
    
    for stock in stocks:
        try:
            # Get latest data for this stock
            data = StockService.get_stock_data(stock.symbol, stock.market)
            
            if data and 'current_price' in data:
                # Update stock in database
                stock.current_price = data['current_price']
                stock.change_percent = data.get('change_percent', 0)
                
                # Calculate updated ROI (Prospect Return) = (EPS / Price) * 100
                if stock.eps and stock.current_price > 0:
                    stock.prospect_return = (stock.eps / stock.current_price) * 100
                
                stock.last_updated = datetime.utcnow()
                
                # Add to result - price, change percent, and ROI for frequent updates
                result[stock.id] = {
                    'current_price': stock.current_price,
                    'change_percent': stock.change_percent,
                    'prospect_return': stock.prospect_return
                }
        except Exception as e:
            print(f"Failed to update {stock.symbol}: {e}")
            
    # Save all updates at once
    db.session.commit()
    
    return jsonify(result)
    
@app.route('/stock_insights/<int:stock_id>', methods=['POST'])
def stock_insights(stock_id):
    """API endpoint for LLM chatbot responses about a stock"""
    stock = Stock.query.get_or_404(stock_id)
    
    # Get user's message from the request
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400
        
    user_message = data['message']
    
    # Get insight from LLM via the service
    response = StockService.get_stock_insights(user_message)
    
    # Get the model ID (fallback to default if not available)
    import os
    model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-7-sonnet-20250219-v1:0')
    
    # Return response as JSON
    return jsonify({
        'response': response,
        'stock_symbol': stock.symbol,
        'stock_name': stock.name,
        'model_id': model_id
    })