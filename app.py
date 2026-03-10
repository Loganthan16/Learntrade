"""
===========================================
  STOCK TRADING LEARNING APP - app.py
  Main Flask Application Entry Point
===========================================
  How to run:
    1. pip install flask
    2. python app.py
    3. Open http://localhost:5000 in browser
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import sqlite3
import os
from datetime import datetime, date

# ── App Setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "trading_secret_2024"   # needed for flash messages

DB_PATH = os.path.join(os.path.dirname(__file__), "trades.db")


# ── Database Helper ────────────────────────────────────────────────────────────
def get_db():
    """Open a database connection and return it."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # lets us access columns by name
    return conn


def init_db():
    """Create tables if they don't exist yet."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS trades (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_name  TEXT    NOT NULL,
            buy_price   REAL    NOT NULL,
            sell_price  REAL,                        -- NULL = open trade
            quantity    INTEGER NOT NULL,
            trade_date  TEXT    NOT NULL,
            trade_type  TEXT    NOT NULL DEFAULT 'Intraday',  -- 'Intraday' | 'Swing'
            reason      TEXT,
            emotion     TEXT,
            pnl         REAL    GENERATED ALWAYS AS (
                            CASE WHEN sell_price IS NOT NULL
                                 THEN (sell_price - buy_price) * quantity
                                 ELSE NULL
                            END
                        ) STORED,
            created_at  TEXT    DEFAULT (datetime('now','localtime'))
        );
    """)
    conn.commit()
    conn.close()


# ── Routes ─────────────────────────────────────────────────────────────────────

# ---------- Dashboard ----------
@app.route("/")
def dashboard():
    conn = get_db()
    c = conn.cursor()

    # total closed trades
    c.execute("SELECT COUNT(*) FROM trades WHERE sell_price IS NOT NULL")
    total_trades = c.fetchone()[0]

    # total P&L across all closed trades
    c.execute("SELECT COALESCE(SUM(pnl), 0) FROM trades WHERE sell_price IS NOT NULL")
    total_pnl = round(c.fetchone()[0], 2)

    # win rate  (trades where pnl > 0)
    c.execute("SELECT COUNT(*) FROM trades WHERE pnl > 0")
    winning = c.fetchone()[0]
    win_rate = round((winning / total_trades * 100), 1) if total_trades else 0

    # today's trades
    today = date.today().isoformat()
    c.execute("""
        SELECT stock_name, buy_price, sell_price, quantity, trade_type, pnl
        FROM trades
        WHERE trade_date = ?
        ORDER BY created_at DESC
    """, (today,))
    today_trades = c.fetchall()

    # today's P&L
    c.execute("SELECT COALESCE(SUM(pnl),0) FROM trades WHERE trade_date=? AND sell_price IS NOT NULL", (today,))
    today_pnl = round(c.fetchone()[0], 2)

    # recent 5 trades (for activity feed)
    c.execute("""
        SELECT stock_name, trade_type, pnl, trade_date
        FROM trades
        WHERE sell_price IS NOT NULL
        ORDER BY created_at DESC LIMIT 5
    """)
    recent_trades = c.fetchall()

    # monthly pnl for sparkline (last 30 days, grouped by date)
    c.execute("""
        SELECT trade_date, ROUND(SUM(pnl),2) AS daily_pnl
        FROM trades
        WHERE sell_price IS NOT NULL
          AND trade_date >= date('now','-30 days')
        GROUP BY trade_date
        ORDER BY trade_date ASC
    """)
    monthly_raw = c.fetchall()
    monthly_labels = [r["trade_date"] for r in monthly_raw]
    monthly_data   = [r["daily_pnl"]  for r in monthly_raw]

    conn.close()

    return render_template("dashboard.html",
        total_trades=total_trades,
        total_pnl=total_pnl,
        win_rate=win_rate,
        today_trades=today_trades,
        today_pnl=today_pnl,
        recent_trades=recent_trades,
        monthly_labels=monthly_labels,
        monthly_data=monthly_data,
    )


# ---------- Add Trade ----------
@app.route("/add", methods=["GET", "POST"])
def add_trade():
    if request.method == "POST":
        # pull every field from the HTML form
        stock_name = request.form["stock_name"].upper().strip()
        buy_price  = float(request.form["buy_price"])
        sell_price_raw = request.form.get("sell_price", "").strip()
        sell_price = float(sell_price_raw) if sell_price_raw else None
        quantity   = int(request.form["quantity"])
        trade_date = request.form["trade_date"]
        trade_type = request.form["trade_type"]
        reason     = request.form.get("reason", "")
        emotion    = request.form.get("emotion", "")

        # basic validation
        if buy_price <= 0 or quantity <= 0:
            flash("Buy price and quantity must be positive numbers.", "error")
            return redirect(url_for("add_trade"))

        conn = get_db()
        conn.execute("""
            INSERT INTO trades
              (stock_name, buy_price, sell_price, quantity, trade_date, trade_type, reason, emotion)
            VALUES (?,?,?,?,?,?,?,?)
        """, (stock_name, buy_price, sell_price, quantity, trade_date, trade_type, reason, emotion))
        conn.commit()
        conn.close()

        flash(f"Trade for {stock_name} added successfully! 🎯", "success")
        return redirect(url_for("journal"))

    # GET – just show the empty form with today's date pre-filled
    return render_template("add_trade.html", today=date.today().isoformat())


# ---------- Trade Journal ----------
@app.route("/journal")
def journal():
    stock_filter = request.args.get("stock", "").strip().upper()
    type_filter  = request.args.get("type", "")
    sort_by      = request.args.get("sort", "created_at")
    sort_dir     = request.args.get("dir", "DESC")

    allowed_sorts = {"created_at", "trade_date", "stock_name", "pnl", "trade_type"}
    if sort_by not in allowed_sorts:
        sort_by = "created_at"
    if sort_dir not in {"ASC", "DESC"}:
        sort_dir = "DESC"

    query  = "SELECT * FROM trades WHERE 1=1"
    params = []

    if stock_filter:
        query += " AND stock_name LIKE ?"
        params.append(f"%{stock_filter}%")
    if type_filter:
        query += " AND trade_type = ?"
        params.append(type_filter)

    query += f" ORDER BY {sort_by} {sort_dir}"

    conn = get_db()
    trades = conn.execute(query, params).fetchall()
    conn.close()

    return render_template("journal.html",
        trades=trades,
        stock_filter=stock_filter,
        type_filter=type_filter,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


# ---------- Delete Trade ----------
@app.route("/delete/<int:trade_id>", methods=["POST"])
def delete_trade(trade_id):
    conn = get_db()
    conn.execute("DELETE FROM trades WHERE id=?", (trade_id,))
    conn.commit()
    conn.close()
    flash("Trade deleted.", "info")
    return redirect(url_for("journal"))


# ---------- Analytics ----------
@app.route("/analytics")
def analytics():
    conn = get_db()
    c = conn.cursor()

    # closed trades only
    c.execute("SELECT COUNT(*) FROM trades WHERE sell_price IS NOT NULL")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM trades WHERE pnl > 0")
    wins = c.fetchone()[0]
    losses = total - wins
    win_rate = round(wins / total * 100, 1) if total else 0

    c.execute("SELECT AVG(pnl) FROM trades WHERE pnl > 0")
    avg_profit = round(c.fetchone()[0] or 0, 2)

    c.execute("SELECT AVG(pnl) FROM trades WHERE pnl < 0")
    avg_loss = round(c.fetchone()[0] or 0, 2)

    c.execute("SELECT MAX(pnl) FROM trades WHERE sell_price IS NOT NULL")
    best_trade = round(c.fetchone()[0] or 0, 2)

    c.execute("SELECT MIN(pnl) FROM trades WHERE sell_price IS NOT NULL")
    worst_trade = round(c.fetchone()[0] or 0, 2)

    # best stock (by total P&L)
    c.execute("""
        SELECT stock_name, ROUND(SUM(pnl),2) AS total_pnl, COUNT(*) AS cnt
        FROM trades
        WHERE sell_price IS NOT NULL
        GROUP BY stock_name
        ORDER BY total_pnl DESC
        LIMIT 5
    """)
    top_stocks = c.fetchall()

    # emotion vs performance
    c.execute("""
        SELECT emotion, ROUND(AVG(pnl),2) AS avg_pnl, COUNT(*) as cnt
        FROM trades
        WHERE sell_price IS NOT NULL AND emotion != ''
        GROUP BY emotion
        ORDER BY avg_pnl DESC
    """)
    emotion_data = c.fetchall()

    # P&L by trade type
    c.execute("""
        SELECT trade_type,
               ROUND(SUM(pnl),2)   AS total_pnl,
               COUNT(*)             AS cnt,
               ROUND(AVG(pnl),2)   AS avg_pnl
        FROM trades
        WHERE sell_price IS NOT NULL
        GROUP BY trade_type
    """)
    type_data = c.fetchall()

    # cumulative P&L over time (for chart)
    c.execute("""
        SELECT trade_date, ROUND(SUM(pnl),2) AS daily
        FROM trades
        WHERE sell_price IS NOT NULL
        GROUP BY trade_date
        ORDER BY trade_date ASC
    """)
    rows = c.fetchall()
    cum_dates, cum_pnl, running = [], [], 0
    for r in rows:
        running += r["daily"]
        cum_dates.append(r["trade_date"])
        cum_pnl.append(round(running, 2))

    conn.close()

    return render_template("analytics.html",
        total=total, wins=wins, losses=losses, win_rate=win_rate,
        avg_profit=avg_profit, avg_loss=avg_loss,
        best_trade=best_trade, worst_trade=worst_trade,
        top_stocks=top_stocks,
        emotion_data=emotion_data,
        type_data=type_data,
        cum_dates=cum_dates,
        cum_pnl=cum_pnl,
    )


# ---------- Charts ----------
@app.route("/charts")
def charts():
    return render_template("charts.html")


# ── Start ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()           # create DB tables on first run
    print("\n🚀  Trading App running at http://localhost:5000\n")
    port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port, debug=False)
```

Click **"Commit changes"** ✅

---

## Step 3 — Deploy on Railway

1. Go to 👉 **https://railway.app**
2. Click **"Login"** → **"Login with GitHub"**
3. Authorize Railway
4. Click **"New Project"**
5. Click **"Deploy from GitHub repo"**
6. Select **"Loganthan16/Learntrade"**
7. Click **"Deploy Now"**

Wait 2 minutes for build to finish ⏳

---

## Step 4 — Get your live URL

1. Click your project on Railway
2. Click **"Settings"** tab
3. Scroll to **"Domains"**
4. Click **"Generate Domain"**
5. Copy the URL like:
```
https://learntrade-production.up.railway.app
