# MyValueLine

My Value Line, a personal stocks portfolio management dashboard.

## Features

- Add and track stocks from US, Hong Kong, and China mainland markets
- View detailed stock information including price, volume, P/E ratio, and more
- Interactive price charts for each stock
- Clean, responsive dashboard interface inspired by Value Line
- Real-time stock data via Yahoo Finance

## Requirements

- Python 3.7+
- Flask
- Flask-SQLAlchemy
- yfinance
- pandas
- plotly
- requests

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/MyValueLine.git
   cd MyValueLine
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install flask flask-sqlalchemy yfinance pandas plotly requests
   ```

## Usage

1. Start the application:
   ```
   python run.py
   ```

2. Open your web browser and go to `http://localhost:5000`

3. Add your first stock to start building your portfolio!

## How It Works

- **Dashboard**: View all your stocks and their performance at a glance
- **Add Stock**: Search for and add stocks from US, Hong Kong, and China markets
- **Stock Details**: View comprehensive data and charts for each stock in your portfolio

## License

This project is licensed under the MIT License - see the LICENSE file for details.