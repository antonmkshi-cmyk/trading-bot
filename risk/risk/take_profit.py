from core.logger import logger

# ==========================================
# TAKE PROFIT SYSTEM
# ==========================================

def check_take_profit(
    portfolio,
    symbol,
    current_price,
    take_profit_percent
):
    if symbol not in portfolio.positions:
        return False

    position = portfolio.positions[symbol]
    entry_price = position["entry_price"]

    current_profit_percent = ((current_price - entry_price) / entry_price) * 100

    logger.info(
        f"Take profit check | "
        f"Current: {round(current_profit_percent, 4)}% | "
        f"Target: {take_profit_percent}%"
    )

    if current_profit_percent >= take_profit_percent:
        logger.warning("TAKE PROFIT TRIGGERED")
        print(f"🟢 TAKE PROFIT | Profit: {round(current_profit_percent, 4)}%")
        portfolio.sell_asset(symbol, current_price)
        return True

    return False