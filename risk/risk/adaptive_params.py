from core.logger import logger

# ==========================================
# ADAPTIVE PARAMETERS (PER STRATEGY + VOLATILITY)
# ==========================================

class AdaptiveParams:
    def __init__(self):
        # SIDEWAYS (SCALP)
        self.scalp_tp = 0.50      # 0.50% — было 0.25
        self.scalp_sl = 0.20      # 0.20%

        # UPTREND (TREND LONG)
        self.trend_tp = 1.00      # 1.00% — было 0.65
        self.trend_sl = 0.40

        # DOWNTREND (SHORT)
        self.short_tp = 1.20      # 0.80% — было 0.50
        self.short_sl = 0.40

        # Текущие (для обратной совместимости)
        self.tp = self.scalp_tp
        self.sl = self.scalp_sl
        self.trailing_stop = self.scalp_sl

    def update(self, trade_history, volatility, market_phase="SIDEWAYS"):
        """Адаптирует параметры для активной стратегии + волатильность"""
        
        from config import MIN_TP_TO_COVER_FEES
        
        # ==========================================
        # БАЗОВЫЕ НАСТРОЙКИ ПОД ФАЗУ РЫНКА
        # ==========================================
        
        if market_phase == "SIDEWAYS":
            self.tp = self.scalp_tp
            self.sl = self.scalp_sl
            
        elif market_phase == "UPTREND":
            self.tp = self.trend_tp
            self.sl = self.trend_sl
            
        elif market_phase == "DOWNTREND":
            self.tp = self.short_tp
            self.sl = self.short_sl

        # ==========================================
        # АДАПТАЦИЯ К ВОЛАТИЛЬНОСТИ (НОВАЯ ЛОГИКА)
        # ==========================================
        
        if volatility < 0.1:
            # Очень низкая волатильность — минимальный TP
            self.tp = max(MIN_TP_TO_COVER_FEES, self.tp * 0.7)
            self.sl = min(0.25, self.sl * 0.8)
            logger.info(f"🐌 Very low volatility ({volatility:.2f}%): TP reduced to {self.tp}%")
            
        elif volatility < 0.3:
            # Низкая волатильность — умеренно
            self.tp = max(MIN_TP_TO_COVER_FEES, self.tp * 0.85)
            logger.info(f"📊 Low volatility ({volatility:.2f}%): TP = {self.tp}%")
            
        elif volatility > 1.0:
            # Высокая волатильность — увеличиваем цели
            self.tp = min(2.0, self.tp * 1.5)
            self.sl = min(0.6, self.sl * 1.2)
            logger.info(f"⚡ High volatility ({volatility:.2f}%): TP increased to {self.tp}%, SL to {self.sl}%")
            
        elif volatility > 0.5:
            # Средняя волатильность
            self.tp = min(1.5, self.tp * 1.2)
            logger.info(f"📈 Medium volatility ({volatility:.2f}%): TP increased to {self.tp}%")

        # ==========================================
        # АДАПТАЦИЯ К WINRATE (ОСТАЕТСЯ)
        # ==========================================
        
        if len(trade_history) >= 10:
            recent = trade_history[-20:] if len(trade_history) >= 20 else trade_history
            wins = [t for t in recent if t["pnl"] > 0]
            winrate = len(wins) / len(recent) * 100 if recent else 50
            
            if winrate < 30:
                self.tp = max(MIN_TP_TO_COVER_FEES, self.tp * 0.8)
                self.sl = min(0.50, self.sl * 1.2)
                logger.info(f"⚠️ Winrate low ({winrate:.1f}%): reducing TP to {self.tp}%, increasing SL to {self.sl}%")
                
            elif winrate > 60:
                self.tp = min(2.0, self.tp * 1.2)
                self.sl = max(0.25, self.sl * 0.8)
                logger.info(f"🎯 Winrate high ({winrate:.1f}%): increasing TP to {self.tp}%, reducing SL to {self.sl}%")
        
        # Гарантируем минимальный TP
        if self.tp < MIN_TP_TO_COVER_FEES:
            self.tp = MIN_TP_TO_COVER_FEES
            logger.info(f"🔒 TP adjusted to minimum {MIN_TP_TO_COVER_FEES}% to cover fees")
        
        self.trailing_stop = self.sl
        return self

    # ==========================================
    # ПРОВЕРКА, МОЖНО ЛИ ТОРГОВАТЬ
    # ==========================================
    
    def can_trade(self, volatility):
        """Возвращает True если условия для торговли подходят"""
        from config import MIN_VOLATILITY_FOR_TRADING
        
        if volatility < MIN_VOLATILITY_FOR_TRADING:
            logger.info(f"⏸️ Volatility too low ({volatility:.2f}% < {MIN_VOLATILITY_FOR_TRADING}%) — trading paused")
            return False
        return True
    
    def set_for_scalp(self):
        self.tp = self.scalp_tp
        self.sl = self.scalp_sl
        self.trailing_stop = self.scalp_sl
        
    def set_for_trend_long(self):
        self.tp = self.trend_tp
        self.sl = self.trend_sl
        self.trailing_stop = self.trend_sl
        
    def set_for_trend_short(self):
        self.tp = self.short_tp
        self.sl = self.short_sl
        self.trailing_stop = self.short_sl