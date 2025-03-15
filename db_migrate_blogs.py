from app import app, db
from app.models import MarkdownBlog

# Create the MarkdownBlog table if it doesn't exist
print("Migrating database: Adding MarkdownBlog table")
with app.app_context():
    db.create_all()
print("Database migration completed successfully!")