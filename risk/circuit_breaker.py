#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# risk/circuit_breaker.py - ащита от больших просадок

import json
import os
from datetime import datetime, date
from core.logger import logger


class CircuitBreaker:
    def __init__(self, daily_limit_percent=5.0, weekly_limit_percent=12.0, consecutive_loss_limit=3):
        """
        daily_limit_percent: дневной лимит просадки в % (например 5 = -5% за день)
        weekly_limit_percent: недельный лимит просадки в %
        consecutive_loss_limit: сколько убытков подряд для паузы
        """
        self.daily_limit = daily_limit_percent
        self.weekly_limit = weekly_limit_percent
        self.consecutive_loss_limit = consecutive_loss_limit
        
        self.daily_pnl = 0.0
        self.weekly_pnl = 0.0
        self.current_day = date.today()
        self.current_week = date.today().isocalendar()[1]
        self.start_balance = None
        
        self.consecutive_losses = 0
        self.is_breached = False
        self.breach_reason = None
        
        self.history_file = "circuit_breaker_history.json"
        self._load_history()
    
    def _load_history(self):
        """агружает сохранённую историю"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.daily_pnl = data.get('daily_pnl', 0.0)
                    self.weekly_pnl = data.get('weekly_pnl', 0.0)
                    self.consecutive_losses = data.get('consecutive_losses', 0)
                logger.info("[CB] Circuit Breaker history loaded")
            except Exception as e:
                logger.warning(f"[CB] Could not load history: {e}")
    
    def _save_history(self):
        """Сохраняет текущее состояние"""
        try:
            data = {
                'daily_pnl': self.daily_pnl,
                'weekly_pnl': self.weekly_pnl,
                'consecutive_losses': self.consecutive_losses,
                'timestamp': datetime.now().isoformat()
            }
            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"[CB] Could not save history: {e}")
    
    def _check_reset(self):
        """роверяет, нужно ли сбросить дневные/недельные счётчики"""
        today = date.today()
        week = today.isocalendar()[1]
        
        if today != self.current_day:
            # овый день
            logger.info(f"[CB] New day: resetting daily PnL (was {self.daily_pnl:.2f} USDT)")
            self.daily_pnl = 0.0
            self.current_day = today
        
        if week != self.current_week:
            # овая неделя
            logger.info(f"[CB] New week: resetting weekly PnL (was {self.weekly_pnl:.2f} USDT)")
            self.weekly_pnl = 0.0
            self.current_week = week
        
        self._save_history()
    
    def set_balance(self, balance):
        """станавливает начальный баланс для расчёта процентов"""
        self.start_balance = balance
        logger.info(f"[CB] Initial balance set: {balance:.2f} USDT")
    
    def register_trade(self, pnl, balance=None):
        """егистрирует сделку и проверяет лимиты"""
        self._check_reset()
        
        if balance and not self.start_balance:
            self.start_balance = balance
        
        self.daily_pnl += pnl
        self.weekly_pnl += pnl
        
        # бновляем счётчик последовательных убытков
        if pnl < 0:
            self.consecutive_losses += 1
            logger.warning(f"[CB] Consecutive losses: {self.consecutive_losses}")
        else:
            self.consecutive_losses = 0
        
        self._save_history()
        return self.check()
    
    def check(self):
        """роверяет, не достигнуты ли лимиты"""
        if self.is_breached:
            return False
        
        # асчёт процентов относительно стартового баланса
        if self.start_balance and self.start_balance > 0:
            daily_loss_pct = abs(self.daily_pnl) / self.start_balance * 100 if self.daily_pnl < 0 else 0
            weekly_loss_pct = abs(self.weekly_pnl) / self.start_balance * 100 if self.weekly_pnl < 0 else 0
        else:
            daily_loss_pct = 0
            weekly_loss_pct = 0
        
        # роверка дневного лимита
        if daily_loss_pct >= self.daily_limit:
            self.is_breached = True
            self.breach_reason = f"Daily loss limit: {daily_loss_pct:.2f}% >= {self.daily_limit}%"
            logger.error(f"[CB] BREACHED: {self.breach_reason}")
            return False
        
        # роверка недельного лимита
        if weekly_loss_pct >= self.weekly_limit:
            self.is_breached = True
            self.breach_reason = f"Weekly loss limit: {weekly_loss_pct:.2f}% >= {self.weekly_limit}%"
            logger.error(f"[CB] BREACHED: {self.breach_reason}")
            return False
        
        # роверка последовательных убытков
        if self.consecutive_losses >= self.consecutive_loss_limit:
            self.is_breached = True
            self.breach_reason = f"Consecutive losses: {self.consecutive_losses} >= {self.consecutive_loss_limit}"
            logger.error(f"[CB] BREACHED: {self.breach_reason}")
            return False
        
        return True
    
    def reset(self):
        """учной сброс защиты"""
        self.is_breached = False
        self.breach_reason = None
        self.consecutive_losses = 0
        self.daily_pnl = 0.0
        self.weekly_pnl = 0.0
        logger.info("[CB] Circuit Breaker manually reset")
        self._save_history()
    
    def get_status(self):
        """озвращает текущий статус"""
        if self.start_balance and self.start_balance > 0:
            daily_loss_pct = abs(self.daily_pnl) / self.start_balance * 100 if self.daily_pnl < 0 else 0
            weekly_loss_pct = abs(self.weekly_pnl) / self.start_balance * 100 if self.weekly_pnl < 0 else 0
        else:
            daily_loss_pct = 0
            weekly_loss_pct = 0
        
        return {
            'is_breached': self.is_breached,
            'breach_reason': self.breach_reason,
            'daily_pnl': self.daily_pnl,
            'weekly_pnl': self.weekly_pnl,
            'daily_loss_pct': daily_loss_pct,
            'weekly_loss_pct': weekly_loss_pct,
            'consecutive_losses': self.consecutive_losses,
            'daily_limit': self.daily_limit,
            'weekly_limit': self.weekly_limit
        }
