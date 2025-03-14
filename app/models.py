from app import db
from datetime import datetime
from sqlalchemy import func

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    chinese_name = db.Column(db.String(100), nullable=True)  # Chinese name for HK/CN stocks
    market = db.Column(db.String(20), nullable=False)  # US, HK, CN
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Track basic information for quick display
    current_price = db.Column(db.Float, nullable=True)
    change_percent = db.Column(db.Float, nullable=True)
    ytd_change_percent = db.Column(db.Float, nullable=True)
    eps = db.Column(db.Float, nullable=True)
    prospect_return = db.Column(db.Float, nullable=True)  # ROI
    roe = db.Column(db.Float, nullable=True)
    last_updated = db.Column(db.DateTime, nullable=True)
    
    # For ordering in the display
    display_order = db.Column(db.Integer, default=lambda: Stock.next_order())
    
    def __repr__(self):
        return f'<Stock {self.symbol}>'
        
    @staticmethod
    def next_order():
        """Get the next available display order number"""
        max_order = db.session.query(func.max(Stock.display_order)).scalar()
        return (max_order or 0) + 1