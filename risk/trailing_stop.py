from core.logger import logger

# ==========================================
# UPDATE TRAILING STOP
# ==========================================

def update_trailing_stop(position, current_price, entry_price):
    """Обновляет максимальную прибыль для трейлинг стопа"""
    
    position_type = position.get("position_type", "LONG")
    
    if position_type == "LONG":
        current_profit_percent = ((current_price - entry_price) / entry_price) * 100
    else:  # SHORT
        current_profit_percent = ((entry_price - current_price) / entry_price) * 100

    if "max_profit" not in position:
        position["max_profit"] = 0.0

    if current_profit_percent > position["max_profit"]:
        position["max_profit"] = current_profit_percent
        logger.info(f"New max profit: {current_profit_percent:.2f}%")

    return current_profit_percent


# ==========================================
# CHECK TRAILING STOP
# ==========================================

def check_trailing_stop(portfolio, symbol, current_price, trailing_stop_percent):
    if symbol not in portfolio.positions:
        return False

    position = portfolio.positions[symbol]
    entry_price = position["entry_price"]
    position_type = position.get("position_type", "LONG")
    
    # Обновляем максимальную прибыль
    current_profit = update_trailing_stop(position, current_price, entry_price)
    max_profit = position.get("max_profit", 0.0)

    drawdown = max_profit - current_profit

    if drawdown >= trailing_stop_percent:
        logger.warning(f"TRAILING STOP TRIGGERED | Type: {position_type} | Max: {max_profit:.2f}% | Current: {current_profit:.2f}% | Drawdown: {drawdown:.2f}%")
        print(f"🟡 TRAILING STOP | {position_type} | Max: {round(max_profit, 2)}% | Current: {round(current_profit, 2)}%")
        return True

    return False


# ==========================================
# RESET TRAILING STOP
# ==========================================

def reset_trailing_stop(portfolio, symbol):
    """Сбрасывает трейлинг стоп при открытии новой позиции"""
    if symbol in portfolio.positions:
        portfolio.positions[symbol]["max_profit"] = 0.0
        logger.info(f"Trailing stop reset for {symbol}")