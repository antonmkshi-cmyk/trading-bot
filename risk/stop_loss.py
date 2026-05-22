from core.logger import logger

# ==========================================
# STOP LOSS SYSTEM
# ==========================================

def check_stop_loss(
    portfolio,
    symbol,
    current_price,
    stop_loss_percent
):
    if symbol not in portfolio.positions:
        return False

    position = portfolio.positions[symbol]
    entry_price = position["entry_price"]

    current_profit_percent = ((current_price - entry_price) / entry_price) * 100

    logger.info(
        f"Stop loss check | "
        f"Current: {round(current_profit_percent, 4)}% | "
        f"Limit: -{stop_loss_percent}%"
    )

    if current_profit_percent <= -stop_loss_percent:
        logger.warning("STOP LOSS TRIGGERED")
        print(f"🔴 STOP LOSS | Loss: {round(current_profit_percent, 4)}%")
        portfolio.sell_asset(symbol, current_price)
        return True

    return False