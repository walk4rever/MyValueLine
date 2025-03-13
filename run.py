from app import app, db
from app.models import Stock
from datetime import datetime

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)