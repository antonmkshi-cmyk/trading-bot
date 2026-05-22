from core.logger import logger

from config import (
    RISK_PER_TRADE,
    MAX_POSITION_SIZE_USDT
)

# ==========================================
# POSITION SIZE CALCULATOR (LEGACY)
# ==========================================

def calculate_position_size(balance, current_price):
    """Простой расчет размера позиции (для обратной совместимости)"""
    risk_amount = (balance * RISK_PER_TRADE) / 100
    
    if risk_amount > MAX_POSITION_SIZE_USDT:
        risk_amount = MAX_POSITION_SIZE_USDT
        logger.info(f"Position limited to {MAX_POSITION_SIZE_USDT} USDT")
    
    btc_amount = risk_amount / current_price
    logger.info(f"Risk amount: {risk_amount}")
    logger.info(f"BTC amount: {btc_amount}")
    
    return round(btc_amount, 6)


# ==========================================
# АДАПТИВНЫЙ РАСЧЕТ РАЗМЕРА ПОЗИЦИИ
# ==========================================

def calculate_adaptive_position_size(balance, current_price, risk_manager):
    """
    Адаптивный расчет размера позиции с учетом всех множителей
    """
    position_usdt = risk_manager.get_position_size_usdt(balance)
    
    # Ограничиваем максимальным значением из config
    if position_usdt > MAX_POSITION_SIZE_USDT:
        position_usdt = MAX_POSITION_SIZE_USDT
        logger.info(f"Position limited by config to {MAX_POSITION_SIZE_USDT} USDT")
    
    btc_amount = position_usdt / current_price
    
    logger.info(f"Adaptive position: {position_usdt:.0f} USDT / {btc_amount:.6f} BTC")
    return round(btc_amount, 8)