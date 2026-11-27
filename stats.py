
import sqlite3
from datetime import datetime, timezone, timedelta

DB_NAME = "radar_stats.db"


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry REAL NOT NULL,
                stop_loss REAL NOT NULL,
                tp1 REAL NOT NULL,
                tp2 REAL NOT NULL,
                tp3 REAL NOT NULL,
                score INTEGER,
                created_at TEXT NOT NULL,
                status TEXT DEFAULT 'OPEN',
                outcome TEXT,
                exit_price REAL,
                closed_at TEXT
            )
        """)
        conn.commit()


def save_signal(item):
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO signals (
                symbol, direction, entry, stop_loss,
                tp1, tp2, tp3, score, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["symbol"],
            item["signal"],
            item["price"],
            item["stop_loss"],
            item["tp1"],
            item["tp2"],
            item["tp3"],
            item["score"],
            now_utc()
        ))
        conn.commit()
        return cursor.lastrowid


def update_signal(signal_id, high, low):
    with get_connection() as conn:
        row = conn.execute("""
            SELECT direction, stop_loss, tp1, tp2, tp3
            FROM signals
            WHERE id = ? AND status = 'OPEN'
        """, (signal_id,)).fetchone()

        if not row:
            return

        direction, sl, tp1, tp2, tp3 = row

        if direction == "LONG":
            if low <= sl:
                outcome, exit_price = "SL", sl
            elif high >= tp3:
                outcome, exit_price = "TP3", tp3
            elif high >= tp2:
                outcome, exit_price = "TP2", tp2
            elif high >= tp1:
                outcome, exit_price = "TP1", tp1
            else:
                return
        else:
            if high >= sl:
                outcome, exit_price = "SL", sl
            elif low <= tp3:
                outcome, exit_price = "TP3", tp3
            elif low <= tp2:
                outcome, exit_price = "TP2", tp2
            elif low <= tp1:
                outcome, exit_price = "TP1", tp1
            else:
                return

        conn.execute("""
            UPDATE signals
            SET status = 'CLOSED',
                outcome = ?,
                exit_price = ?,
                closed_at = ?
            WHERE id = ?
        """, (outcome, exit_price, now_utc(), signal_id))

        conn.commit()


def get_statistics(days=14):
    since = (datetime.now(timezone.utc) -
             timedelta(days=days)).isoformat()

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT outcome, COUNT(*)
            FROM signals
            WHERE created_at >= ?
            AND status = 'CLOSED'
            GROUP BY outcome
        """, (since,)).fetchall()

        total = sum(count for _, count in rows)
        wins = sum(count for outcome, count in rows
                   if outcome in ("TP1", "TP2", "TP3"))
        losses = sum(count for outcome, count in rows
                     if outcome == "SL")

        win_rate = wins / total * 100 if total else 0

        return {
            "period_days": days,
            "total": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 2),
            "results": dict(rows)
        }


def format_report(days=14):
    stats = get_statistics(days)

    return (
        f"BINANCE RADAR - {days} DAYS\n\n"
        f"Closed signals: {stats['total']}\n"
        f"Wins: {stats['wins']}\n"
        f"Losses: {stats['losses']}\n"
        f"Win Rate: {stats['win_rate']}%\n"
        f"Results: {stats['results']}"
    )


init_db()
