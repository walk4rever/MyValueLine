from app import db
from datetime import datetime

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    market = db.Column(db.String(20), nullable=False)  # US, HK, CN
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Track basic information for quick display
    current_price = db.Column(db.Float, nullable=True)
    change_percent = db.Column(db.Float, nullable=True)
    last_updated = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Stock {self.symbol}>'