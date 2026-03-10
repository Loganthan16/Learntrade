# 📈 TradeLog — Stock Trading Learning App

A beginner-friendly intraday/swing trade tracker built with Flask + SQLite.
Track your trades, analyse your patterns, and **learn from every rupee**.

---

## 🗂️ Project Structure

```
trading_app/
├── app.py                 ← Flask routes & backend logic
├── trades.db              ← SQLite database (auto-created on first run)
├── requirements.txt       ← Python dependencies
├── README.md              ← This file
├── static/
│   ├── css/
│   │   └── style.css      ← All styles (dark terminal theme)
│   └── js/
│       └── main.js        ← Shared JS (market status, flash messages)
└── templates/
    ├── base.html          ← Layout with sidebar navigation
    ├── dashboard.html     ← KPIs + 30-day chart + today's trades
    ├── add_trade.html     ← Trade entry form
    ├── journal.html       ← Searchable trade table
    ├── analytics.html     ← Deep stats & charts
    └── charts.html        ← TradingView live charts
```

---

## ⚡ Setup — Step by Step

### Step 1 — Make sure Python is installed
```bash
python --version        # should be 3.8 or higher
```

### Step 2 — Navigate to the project folder
```bash
cd trading_app
```

### Step 3 — (Recommended) Create a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 4 — Install dependencies
```bash
pip install -r requirements.txt
```
That's it — only Flask is needed!

### Step 5 — Run the app
```bash
python app.py
```

### Step 6 — Open in browser
```
http://localhost:5000
```

The SQLite database (`trades.db`) is created automatically on first run.

---

## 🗃️ Database Schema

```sql
CREATE TABLE trades (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_name  TEXT    NOT NULL,          -- e.g. RELIANCE, NIFTY50
    buy_price   REAL    NOT NULL,          -- entry price in ₹
    sell_price  REAL,                      -- exit price (NULL = open trade)
    quantity    INTEGER NOT NULL,          -- number of shares
    trade_date  TEXT    NOT NULL,          -- YYYY-MM-DD
    trade_type  TEXT    NOT NULL,          -- 'Intraday' | 'Swing'
    reason      TEXT,                      -- why you took the trade
    emotion     TEXT,                      -- your emotion during the trade
    pnl         REAL GENERATED ALWAYS AS ( -- auto-calculated
                    CASE WHEN sell_price IS NOT NULL
                         THEN (sell_price - buy_price) * quantity
                         ELSE NULL
                    END
                ) STORED,
    created_at  TEXT DEFAULT (datetime('now','localtime'))
);
```

---

## 📱 Features at a Glance

| Page       | What it does                                              |
|------------|-----------------------------------------------------------|
| Dashboard  | KPI cards, 30-day bar chart, recent activity feed         |
| Add Trade  | Form with live P&L preview, emotion picker                |
| Journal    | Full trade history, filter by stock/type, sort by P&L     |
| Analytics  | Win rate, cumulative curve, top stocks, emotion impact    |
| Charts     | Embedded TradingView widget — real NSE/BSE live charts    |

---

## 🚀 Future Upgrades (Roadmap)

### 1. 📡 Real-Time Stock Data API
Integrate a market data API to auto-fill current price:

```python
# Option A: yfinance (free, unofficial Yahoo Finance)
pip install yfinance
import yfinance as yf
ticker = yf.Ticker("RELIANCE.NS")
price = ticker.fast_info['lastPrice']

# Option B: Zerodha Kite Connect (official, paid)
# Gives live streaming data, order placement, portfolio

# Option C: NSEpy (free NSE historical data)
pip install nsepy
```

Add an `/api/price/<symbol>` Flask endpoint and call it via JS `fetch()` on the Add Trade page to auto-fill buy price.

---

### 2. 📊 Backtesting Strategies
Add a strategy tester to see how a rule would have performed on past data:

```python
# Using Backtrader library
pip install backtrader

# Example: Simple Moving Average crossover backtest
import backtrader as bt

class SMACross(bt.Strategy):
    def __init__(self):
        sma1 = bt.ind.SMA(period=10)
        sma2 = bt.ind.SMA(period=30)
        self.crossover = bt.ind.CrossOver(sma1, sma2)

    def next(self):
        if self.crossover > 0:    # golden cross → buy
            self.buy()
        elif self.crossover < 0:  # death cross → sell
            self.sell()
```

Add a `/backtest` Flask page where you pick a stock and date range.

---

### 3. 🤖 Machine Learning Predictions
Use your trade journal as training data:

```python
pip install scikit-learn pandas

# Features: buy_price, quantity, trade_type, emotion_encoded, day_of_week
# Target: did the trade win? (1/0)

from sklearn.ensemble import RandomForestClassifier
import pandas as pd

# Load trades from DB
df = pd.read_sql("SELECT * FROM trades WHERE sell_price IS NOT NULL", conn)
df["won"] = (df["pnl"] > 0).astype(int)

# Simple model
X = df[["buy_price", "quantity"]]   # add more features over time
y = df["won"]

model = RandomForestClassifier()
model.fit(X, y)
# predict win probability for a new trade
prob = model.predict_proba([[buy_price, qty]])[0][1]
```

Show "Win Probability: 67%" on the Add Trade page as a hint.

---

### 4. 🤖 Trading Bot Automation
Connect to Zerodha Kite Connect for automated order execution:

```python
pip install kiteconnect

from kiteconnect import KiteConnect
kite = KiteConnect(api_key="YOUR_KEY")

# Place a market buy order
order_id = kite.place_order(
    tradingsymbol="RELIANCE",
    exchange=kite.EXCHANGE_NSE,
    transaction_type=kite.TRANSACTION_TYPE_BUY,
    quantity=10,
    product=kite.PRODUCT_MIS,         # MIS = intraday
    order_type=kite.ORDER_TYPE_MARKET,
    variety=kite.VARIETY_REGULAR,
)
```

⚠️ **Warning for beginners:** Never automate real money trades until you have 6+ months of consistent manual profitability and understand the code completely.

---

### 5. 📤 Export to Excel / CSV
Add a download button for your trade journal:

```python
import csv, io
from flask import send_file

@app.route("/export")
def export_csv():
    conn = get_db()
    trades = conn.execute("SELECT * FROM trades").fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID","Stock","Buy","Sell","Qty","Date","Type","P&L","Reason","Emotion"])
    for t in trades:
        writer.writerow([t["id"], t["stock_name"], t["buy_price"], ...])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        download_name="trades.csv",
        as_attachment=True)
```

---

### 6. 🔐 Login System (Multi-user)
Add Flask-Login for user accounts:

```bash
pip install flask-login flask-bcrypt
```

This lets multiple family members or friends each have their own journal.

---

## 💡 Trading Tips for Beginners

1. **Risk max 1-2% per trade** on ₹5000–₹10000 capital = ₹50–₹200 max loss per trade
2. **Always write your reason** before taking a trade — if you can't explain it, don't take it
3. **Track your emotions** — FOMO and fear are the #1 reasons beginners lose money
4. **Review your journal weekly** — patterns (good and bad) become obvious quickly
5. **Paper trade first** — practice with fake money before risking real capital
6. **Never average down** on a losing intraday trade

---

## 📞 Support

This is a personal learning tool. For questions about the code, check:
- Flask docs: https://flask.palletsprojects.com
- SQLite docs: https://www.sqlite.org/docs.html
- TradingView widgets: https://www.tradingview.com/widget/
