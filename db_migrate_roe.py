from app import app, db
from sqlalchemy import text

def run_migration():
    with app.app_context():
        # Add ROE column if it doesn't exist
        try:
            db.session.execute(text("ALTER TABLE stock ADD COLUMN roe FLOAT"))
            print("Added ROE column")
        except Exception as e:
            print(f"Error adding ROE column: {e}")
            
        # Commit changes
        db.session.commit()

if __name__ == "__main__":
    run_migration()