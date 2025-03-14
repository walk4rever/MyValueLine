from app import app, db
import sqlalchemy as sa
from sqlalchemy import text

def run_migration():
    with app.app_context():
        # Add ytd_change_percent column if it doesn't exist
        try:
            db.session.execute(text("ALTER TABLE stock ADD COLUMN ytd_change_percent FLOAT"))
            print("Added ytd_change_percent column")
        except Exception as e:
            print(f"Error adding ytd_change_percent column: {e}")
            
        # Add display_order column if it doesn't exist
        try:
            db.session.execute(text("ALTER TABLE stock ADD COLUMN display_order INTEGER"))
            print("Added display_order column")
        except Exception as e:
            print(f"Error adding display_order column: {e}")
            
        # Set initial display_order values for existing rows
        try:
            # Get all existing stocks
            result = db.session.execute(text("SELECT id FROM stock ORDER BY id"))
            stocks = result.fetchall()
            
            # Update each stock with a sequential display_order
            for i, (stock_id,) in enumerate(stocks):
                db.session.execute(text(f"UPDATE stock SET display_order = {i+1} WHERE id = {stock_id}"))
                
            # Commit all changes
            db.session.commit()
            print(f"Updated display_order for {len(stocks)} stocks")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error updating display_order values: {e}")

if __name__ == "__main__":
    run_migration()