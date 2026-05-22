from core.logger import logger

# ==========================================
# DAILY LOSS LIMIT
# ==========================================

class DailyLossLimit:
    def __init__(self, max_loss_percent=2.0):
        self.max_loss_percent = max_loss_percent
        self.daily_pnl = 0.0

    def register_trade(self, pnl):
        self.daily_pnl += pnl
        logger.info(f"Daily PnL: {round(self.daily_pnl, 4)} USDT")

    def is_allowed(self, start_balance):
        if self.daily_pnl >= 0:
            return True
        current_loss_percent = abs(self.daily_pnl) / start_balance * 100
        if current_loss_percent >= self.max_loss_percent:
            logger.warning(f"DAILY LOSS LIMIT REACHED: {round(current_loss_percent, 2)}%")
            return False
        return True

    def reset(self):
        logger.info("Daily loss limit reset")
        self.daily_pnl = 0.0