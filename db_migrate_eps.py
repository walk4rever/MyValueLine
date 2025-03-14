from app import app, db
from sqlalchemy import text

def run_migration():
    with app.app_context():
        # Add eps column if it doesn't exist
        try:
            db.session.execute(text("ALTER TABLE stock ADD COLUMN eps FLOAT"))
            print("Added eps column")
        except Exception as e:
            print(f"Error adding eps column: {e}")
            
        # Add prospect_return column if it doesn't exist
        try:
            db.session.execute(text("ALTER TABLE stock ADD COLUMN prospect_return FLOAT"))
            print("Added prospect_return column")
        except Exception as e:
            print(f"Error adding prospect_return column: {e}")
            
        # Commit all changes
        db.session.commit()

if __name__ == "__main__":
    run_migration()