# core/state.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
СОХРАНЕНИЕ СОСТОЯНИЯ БОТА
Позволяет восстановить позицию после перезапуска
"""

import json
from pathlib import Path
from datetime import datetime
from core.logger import logger

STATE_FILE = "bot_state.json"


def save_state(portfolio, position_type, cycles_in_position, current_price=None):
    """Сохраняет текущее состояние бота"""
    try:
        state = {
            'balance': portfolio.balance,
            'position_type': position_type,
            'cycles_in_position': cycles_in_position,
            'timestamp': datetime.now().isoformat(),
            'trade_history_count': len(portfolio.trade_history)
        }
        
        # Если есть открытая позиция
        if position_type and position_type in ["LONG", "SHORT"] and portfolio.positions:
            for symbol, pos in portfolio.positions.items():
                state['open_position'] = {
                    'symbol': symbol,
                    'position_type': pos.get('position_type', position_type),
                    'entry_price': pos['entry_price'],
                    'amount': pos['amount'],
                    'commission': pos.get('commission', 0)
                }
                if current_price:
                    state['current_price'] = current_price
                break
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"💾 State saved: balance={portfolio.balance:.2f}, position={position_type}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save state: {e}")
        return False


def load_state():
    """Загружает сохранённое состояние"""
    if not Path(STATE_FILE).exists():
        logger.info("No saved state found")
        return None
    
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        
        logger.info(f"📂 State loaded: balance={state.get('balance')}, position={state.get('position_type')}")
        return state
        
    except Exception as e:
        logger.error(f"Failed to load state: {e}")
        return None


def clear_state():
    """Удаляет сохранённое состояние"""
    try:
        if Path(STATE_FILE).exists():
            Path(STATE_FILE).unlink()
            logger.info("🗑️ State cleared")
    except Exception as e:
        logger.error(f"Failed to clear state: {e}")