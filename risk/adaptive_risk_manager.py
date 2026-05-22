# risk/adaptive_risk_manager.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
АДАПТИВНЫЙ РИСК-МЕНЕДЖЕР V2
- Адаптация под время суток и день недели
- Непрерывная адаптация под волатильность
- Kelly Criterion для размера позиции
"""

from datetime import datetime
from core.logger import logger


class AdaptiveRiskManagerV2:
    def __init__(self):
        # Базовые настройки
        self.base_risk_percent = 5.0      # 5% от баланса на сделку
        self.min_position_usdt = 30
        self.max_position_usdt = 300
        
        # История для адаптации
        self.trade_history = []
        self.winrate_history = []
        self.consecutive_losses = 0
        self.consecutive_wins = 0
        
        # Множители
        self.volatility_multiplier = 1.0
        self.time_multiplier = 1.0
        self.day_multiplier = 1.0
        self.winrate_multiplier = 1.0
        self.streak_multiplier = 1.0
        
        # Статистика
        self.total_trades = 0
        self.winning_trades = 0
        
    def update(self, trade_history, volatility, market_phase):
        """Обновляет все множители на основе истории"""
        self.trade_history = trade_history
        self.total_trades = len(trade_history)
        
        # 1. Обновляем winrate (скользящее окно 20 сделок)
        self._update_winrate_multiplier()
        
        # 2. Обновляем множитель волатильности (непрерывный)
        self._update_volatility_multiplier(volatility)
        
        # 3. Обновляем временной множитель
        self._update_time_multiplier()
        
        # 4. Обновляем дневной множитель
        self._update_day_multiplier()
        
        # 5. Обновляем множитель серии
        self._update_streak_multiplier()
        
        # 6. Адаптация под фазу рынка
        self._update_phase_multiplier(market_phase)
        
        logger.info(f"📊 Risk multipliers: vol={self.volatility_multiplier:.2f}, "
                   f"time={self.time_multiplier:.2f}, day={self.day_multiplier:.2f}, "
                   f"wr={self.winrate_multiplier:.2f}, streak={self.streak_multiplier:.2f}")
        
        return self
    
    def _update_winrate_multiplier(self):
        """Адаптация на основе winrate (Kelly Criterion приближение)"""
        if self.total_trades >= 10:
            # Скользящее окно последних 20 сделок
            recent = self.trade_history[-20:] if self.total_trades >= 20 else self.trade_history
            wins = [t for t in recent if t["pnl"] > 0]
            winrate = len(wins) / len(recent)
            
            # Средний профит / средний убыток
            winning_trades = [t["pnl"] for t in recent if t["pnl"] > 0]
            losing_trades = [t["pnl"] for t in recent if t["pnl"] < 0]
            
            avg_win = sum(winning_trades) / len(winning_trades) if winning_trades else 0
            avg_loss = abs(sum(losing_trades) / len(losing_trades)) if losing_trades else 1
            
            if avg_loss > 0:
                # Kelly Criterion (упрощённый)
                kelly = (winrate * avg_win - (1 - winrate) * avg_loss) / avg_win
                kelly = max(0, min(0.25, kelly))  # Ограничиваем 0-25%
                
                # Преобразуем Kelly в множитель (база 5% -> kelly 0.1 = множитель 1.0)
                self.winrate_multiplier = min(1.5, max(0.5, kelly / 0.1))
            else:
                self.winrate_multiplier = 1.0
            
            logger.info(f"📈 Winrate: {winrate*100:.1f}%, Kelly: {kelly:.3f}, multiplier: {self.winrate_multiplier:.2f}")
    
    def _update_volatility_multiplier(self, volatility):
        """Непрерывная адаптация под волатильность"""
        if volatility < 0.08:
            self.volatility_multiplier = 0.4   # Очень тихо
        elif volatility < 0.15:
            self.volatility_multiplier = 0.6   # Тихо
        elif volatility < 0.25:
            self.volatility_multiplier = 0.8   # Нормально
        elif volatility < 0.40:
            self.volatility_multiplier = 1.0   # Хорошо
        elif volatility < 0.60:
            self.volatility_multiplier = 1.2   # Активно
        elif volatility < 1.0:
            self.volatility_multiplier = 1.4   # Очень активно
        else:
            self.volatility_multiplier = 0.5   # Шторм — снижаем риск
        
        logger.info(f"⚡ Volatility: {volatility:.2f}%, multiplier: {self.volatility_multiplier:.2f}")
    
    def _update_time_multiplier(self):
        """Адаптация под время суток"""
        hour = datetime.now().hour
        
        # Азиатская сессия (низкая волатильность)
        if 2 <= hour <= 7:
            self.time_multiplier = 0.5
            logger.info(f"🕐 Asian session ({hour}h): risk reduced to 0.5x")
        # Европейская сессия (средняя)
        elif 8 <= hour <= 13:
            self.time_multiplier = 0.8
            logger.info(f"🕐 European session ({hour}h): risk 0.8x")
        # Лондонская сессия (высокая)
        elif 14 <= hour <= 17:
            self.time_multiplier = 1.3
            logger.info(f"🕐 London session ({hour}h): risk increased to 1.3x")
        # Нью-Йоркская сессия (максимум)
        elif 18 <= hour <= 22:
            self.time_multiplier = 1.5
            logger.info(f"🕐 New York session ({hour}h): risk increased to 1.5x")
        # Ночная сессия
        else:
            self.time_multiplier = 0.6
            logger.info(f"🕐 Night session ({hour}h): risk reduced to 0.6x")
    
    def _update_day_multiplier(self):
        """Адаптация под день недели"""
        weekday = datetime.now().weekday()
        
        # Понедельник (часто волатильный)
        if weekday == 0:
            self.day_multiplier = 1.2
            logger.info("📅 Monday: risk increased to 1.2x")
        # Вторник-среда (спокойные)
        elif weekday in [1, 2]:
            self.day_multiplier = 0.9
            logger.info("📅 Tue/Wed: risk reduced to 0.9x")
        # Четверг (активный)
        elif weekday == 3:
            self.day_multiplier = 1.1
            logger.info("📅 Thursday: risk increased to 1.1x")
        # Пятница (очень волатильная)
        elif weekday == 4:
            self.day_multiplier = 1.3
            logger.info("📅 Friday: risk increased to 1.3x")
        # Выходные (низкая ликвидность)
        else:
            self.day_multiplier = 0.4
            logger.info("📅 Weekend: risk reduced to 0.4x")
    
    def _update_streak_multiplier(self):
        """Адаптация под серию убытков/прибылей"""
        if self.consecutive_losses >= 3:
            self.streak_multiplier = max(0.3, 1.0 - self.consecutive_losses * 0.15)
            logger.info(f"⚠️ {self.consecutive_losses} losses in row: streak multiplier = {self.streak_multiplier:.2f}")
        elif self.consecutive_wins >= 3:
            self.streak_multiplier = min(1.5, 1.0 + self.consecutive_wins * 0.1)
            logger.info(f"🎯 {self.consecutive_wins} wins in row: streak multiplier = {self.streak_multiplier:.2f}")
        else:
            self.streak_multiplier = 1.0
    
    def _update_phase_multiplier(self, market_phase):
        """Адаптация под фазу рынка"""
        if market_phase == "UPTREND":
            self.phase_multiplier = 1.2
        elif market_phase == "DOWNTREND":
            self.phase_multiplier = 1.1
        else:  # SIDEWAYS
            self.phase_multiplier = 0.8
    
    def register_trade(self, pnl):
        """Регистрирует сделку для обновления серий"""
        if pnl < 0:
            self.consecutive_losses += 1
            self.consecutive_wins = 0
        else:
            self.consecutive_wins += 1
            self.consecutive_losses = 0
        
        self.winning_trades += 1 if pnl > 0 else 0
        
        # Обновляем историю winrate
        self.winrate_history.append(1 if pnl > 0 else 0)
        if len(self.winrate_history) > 50:
            self.winrate_history.pop(0)
    
    def get_position_size_usdt(self, balance):
        """Возвращает размер позиции в USDT"""
        # Базовый размер
        base_size = balance * self.base_risk_percent / 100
        
        # Суммарный множитель
        total_multiplier = (self.volatility_multiplier * self.time_multiplier * 
                           self.day_multiplier * self.winrate_multiplier * 
                           self.streak_multiplier * self.phase_multiplier)
        
        # Применяем
        position_size = base_size * total_multiplier
        
        # Ограничиваем
        position_size = max(self.min_position_usdt, min(self.max_position_usdt, position_size))
        
        logger.info(f"💰 Position size: {position_size:.0f} USDT "
                   f"(base: {base_size:.0f}, mult: {total_multiplier:.2f})")
        
        return round(position_size, 2)
    
    def reset_streak(self):
        """Сброс счётчиков"""
        self.consecutive_losses = 0
        self.consecutive_wins = 0
        logger.info("🔄 Streak counters reset")


# Для обратной совместимости
AdaptiveRiskManager = AdaptiveRiskManagerV2