# infrastructure/database.py
"""
DATABASE LAYER
Обёртка над существующей БД
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Пытаемся использовать существующую БД
try:
    from database.trade_db import save_trade as _save_trade
    from database.trade_db import initialize_database as _init_db
    from database.trade_db import get_connection as _get_conn
    
    class _Database:
        def __init__(self):
            self._initialized = False
        
        def ensure_initialized(self):
            if not self._initialized:
                _init_db()
                self._initialized = True
        
        def save_trade(self, symbol, side, amount, price, fee, pnl, balance_after, position_type=None):
            self.ensure_initialized()
            return _save_trade(symbol, side, amount, price, fee, pnl, balance_after)
        
        def get_connection(self):
            self.ensure_initialized()
            return _get_conn()
        
        def get_statistics(self):
            """Получает статистику из БД"""
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM trades")
            total = cursor.fetchone()[0]
            cursor.execute("SELECT SUM(pnl) FROM trades")
            total_pnl = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM trades WHERE pnl > 0")
            wins = cursor.fetchone()[0]
            conn.close()
            return {
                'total_trades': total,
                'total_pnl': total_pnl,
                'winrate': wins / total * 100 if total > 0 else 0,
                'wins': wins,
                'losses': total - wins
            }
    
    db = _Database()
    print("✅ Using existing database/trade_db.py")

except ImportError:
    # Создаём свою простую БД
    import sqlite3
    from datetime import datetime
    
    class _Database:
        def __init__(self, db_path="trading_data_new.db"):
            self.db_path = PROJECT_ROOT / db_path
            self._init_tables()
        
        def _init_tables(self):
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        symbol TEXT,
                        side TEXT,
                        amount REAL,
                        price REAL,
                        fee REAL,
                        pnl REAL,
                        balance_after REAL,
                        position_type TEXT
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS signals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        signal TEXT,
                        price REAL,
                        volatility REAL,
                        adx REAL,
                        was_taken BOOLEAN DEFAULT 0
                    )
                """)
                conn.commit()
            print(f"✅ Created new database at {self.db_path}")
        
        def save_trade(self, symbol, side, amount, price, fee, pnl, balance_after, position_type=None):
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO trades (symbol, side, amount, price, fee, pnl, balance_after, position_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (symbol, side, amount, price, fee, pnl, balance_after, position_type))
                conn.commit()
        
        def save_signal(self, signal, price, volatility, adx, was_taken=False):
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO signals (signal, price, volatility, adx, was_taken)
                    VALUES (?, ?, ?, ?, ?)
                """, (signal, price, volatility, adx, was_taken))
                conn.commit()
        
        def get_connection(self):
            return sqlite3.connect(self.db_path)
        
        def get_statistics(self):
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM trades")
                total = cursor.fetchone()[0]
                cursor.execute("SELECT SUM(pnl) FROM trades")
                total_pnl = cursor.fetchone()[0] or 0
                cursor.execute("SELECT COUNT(*) FROM trades WHERE pnl > 0")
                wins = cursor.fetchone()[0]
                return {
                    'total_trades': total,
                    'total_pnl': total_pnl,
                    'winrate': wins / total * 100 if total > 0 else 0,
                    'wins': wins,
                    'losses': total - wins
                }
    
    db = _Database()
    print("✅ Created new database (trade_db.py not found)")

print(f"💾 Database ready: {db.__class__.__name__}")