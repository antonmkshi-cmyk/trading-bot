#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# risk/recovery_manager.py - правление восстановлением монет

import time
from datetime import datetime
from core.logger import logger


class RecoveryManager:
    def __init__(self):
        self.recovery_status = {}  # coin -> {'phase': 'active'/'cooldown'/'recovering', 'until': timestamp}
        self.original_strategies = {}  # coin -> какая стратегия была
        self.alternative_strategies = {}  # coin -> альтернативная стратегия
    
    def register_coin(self, coin, main_strategy="TREND_FOLLOWER", alt_strategy="FLAT_SNIPER"):
        """егистрирует монету с основным и альтернативным подходом"""
        self.recovery_status[coin] = {'phase': 'active', 'until': None}
        self.original_strategies[coin] = main_strategy
        self.alternative_strategies[coin] = alt_strategy
        logger.info(f"[RECOVERY] {coin} registered (main: {main_strategy}, alt: {alt_strategy})")
    
    def handle_breach(self, coin, loss_percent, current_strategy):
        """брабатывает падение монеты"""
        logger.warning(f"[RECOVERY] {coin} breached at {loss_percent:.2f}% loss using {current_strategy}")
        
        # 1. сли стратегия была основной → переключаем на альтернативную
        if current_strategy == self.original_strategies[coin]:
            new_strategy = self.alternative_strategies[coin]
            logger.info(f"[RECOVERY] {coin}: switching from {current_strategy} to {new_strategy}")
            self.recovery_status[coin] = {'phase': 'recovering', 'until': None}
            return new_strategy
        
        # 2. сли уже была альтернатива — отправляем в паузу
        elif current_strategy == self.alternative_strategies[coin]:
            cooldown_minutes = 30
            until = time.time() + cooldown_minutes * 60
            self.recovery_status[coin] = {'phase': 'cooldown', 'until': until}
            logger.info(f"[RECOVERY] {coin}: both strategies failed, cooling down for {cooldown_minutes} min")
            return None
        
        # 3. сли пауза уже была — ждём ещё
        else:
            return None
    
    def check_recovery(self, coin, current_strategy):
        """роверяет, можно ли вернуть монету в строй"""
        status = self.recovery_status.get(coin)
        if not status:
            return current_strategy
        
        # сли в активном режиме — всё ок
        if status['phase'] == 'active':
            return current_strategy
        
        # сли в режиме восстановления — используем альтернативную стратегию
        if status['phase'] == 'recovering':
            # осле 3 успешных циклов без убытка возвращаем основную
            # (это будет отслеживать основной движок)
            return self.alternative_strategies[coin]
        
        # сли в режиме паузы (cooldown)
        if status['phase'] == 'cooldown':
            if status['until'] and time.time() > status['until']:
                # ауза кончилась, пробуем основную стратегию снова
                self.recovery_status[coin] = {'phase': 'active', 'until': None}
                logger.info(f"[RECOVERY] {coin}: cooldown finished, back to {self.original_strategies[coin]}")
                return self.original_strategies[coin]
            else:
                # сё ещё на паузе
                return None
        
        return current_strategy
    
    def record_success(self, coin, strategy_used, pnl):
        """аписывает успешную сделку (для выхода из recovery режима)"""
        status = self.recovery_status.get(coin)
        if not status:
            return
        
        # сли были в режиме восстановления и сделка прибыльная
        if status['phase'] == 'recovering' and pnl > 0:
            # осле 3 прибыльных сделок возвращаем основную стратегию
            # то будет делать основной движок
            logger.info(f"[RECOVERY] {coin}: profitable trade in recovery mode")
