from core.logger import logger
from core.config import (
    MAX_POSITION_SIZE,
    MAX_DAILY_LOSS
)

# ==========================================
# RISK MANAGER
# ==========================================

class RiskManager:

    def __init__(self):

        self.daily_loss = 0

    # ==========================================
    # POSITION SIZE CHECK
    # ==========================================

    def check_position_size(self, amount):

        logger.info(
            f"Checking position size: {amount}"
        )

        if amount > MAX_POSITION_SIZE:

            logger.warning(
                "Position size exceeds limit"
            )

            return False

        return True

    # ==========================================
    # DAILY LOSS CHECK
    # ==========================================

    def check_daily_loss(self):

        logger.info(
            f"Current daily loss: {self.daily_loss}"
        )

        if self.daily_loss >= MAX_DAILY_LOSS:

            logger.warning(
                "Daily loss limit reached"
            )

            return False

        return True

    # ==========================================
    # REGISTER LOSS
    # ==========================================

    def register_loss(self, amount):

        logger.warning(
            f"Registering loss: {amount}"
        )

        self.daily_loss += amount

    # ==========================================
    # RESET DAILY LOSS
    # ==========================================

    def reset_daily_loss(self):

        logger.info(
            "Resetting daily loss"
        )

        self.daily_loss = 0
        # ==========================================
# ЗАЩИТА ОТ СЕРИИ УБЫТКОВ
# ==========================================

class ConsecutiveLossProtection:
    def __init__(self, limit=3):
        self.limit = limit
        self.consecutive_losses = 0
        self.is_protection_active = False
    
    def register_trade(self, pnl):
        """Регистрирует сделку и проверяет серию убытков"""
        if pnl < 0:
            self.consecutive_losses += 1
            print(f"⚠️ Убыточная сделка #{self.consecutive_losses}")
        else:
            if self.consecutive_losses > 0:
                print(f"✅ Прибыльная сделка — сброс счетчика убытков")
            self.consecutive_losses = 0
        
        if self.consecutive_losses >= self.limit:
            self.is_protection_active = True
            print(f"🛑 ЗАЩИТА АКТИВИРОВАНА: {self.consecutive_losses} убытка подряд")
        else:
            self.is_protection_active = False
        
        return self.is_protection_active
    
    def reset(self):
        """Ручной сброс защиты"""
        self.consecutive_losses = 0
        self.is_protection_active = False
        print("🟢 ЗАЩИТА СБРОШЕНА")