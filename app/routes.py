from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from app.models import Stock
from app.stock_service import StockService
from datetime import datetime
import json

@app.route('/')
def index():
    """Display the portfolio dashboard"""
    stocks = Stock.query.all()
    
    # Update latest prices for all stocks
    for stock in stocks:
        try:
            # Only update if it's been a while since last update
            if not stock.last_updated or (datetime.utcnow() - stock.last_updated).seconds > 3600:
                data = StockService.get_stock_data(stock.symbol, stock.market)
                if data and 'current_price' in data:
                    stock.current_price = data['current_price']
                    stock.change_percent = data.get('change_percent', 0)
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
            market=market,
            current_price=stock_data.get('current_price'),
            change_percent=stock_data.get('change_percent'),
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