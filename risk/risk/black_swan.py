from core.logger import logger

# ==========================================
# BLACK SWAN PROTECTION
# ==========================================

def check_black_swan(price_history, current_price, threshold=2.0):
    """
    Если цена упала на threshold% за последние 5 циклов (50 секунд) — экстренный выход.
    """
    if len(price_history) < 5:
        return False

    price_5_ago = price_history[-5]
    drop_percent = (price_5_ago - current_price) / price_5_ago * 100

    if drop_percent >= threshold:
        logger.warning(f"BLACK SWAN DETECTED: {round(drop_percent, 2)}% drop in 50 seconds")
        return True

    return False