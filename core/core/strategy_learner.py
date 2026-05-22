#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# core/strategy_learner.py - бучение: какие стратегии оставить

from collections import deque
from core.logger import logger


class StrategyLearner:
    """чится на истории сделок и отбирает лучшие стратегии"""
    
    def __init__(self, min_trades_for_decision=10):
        self.min_trades = min_trades_for_decision
        self.strategy_stats = {}  # coin -> {strategy -> stats}
        
        # араметры отсева
        self.min_winrate = 0.40      # ниже 40% — стратегия плохая
        self.good_winrate = 0.55     # выше 55% — стратегия хорошая
        self.max_consecutive_losses = 3  # 3 убытка подряд → стоп
        
        logger.info("=== STRATEGY LEARNER INITIALIZED ===")
    
    def init_coin(self, coin, strategies):
        """нициализирует статистику для новой монеты"""
        if coin not in self.strategy_stats:
            self.strategy_stats[coin] = {}
            for strategy in strategies:
                self.strategy_stats[coin][strategy] = {
                    'wins': 0,
                    'losses': 0,
                    'total_pnl': 0.0,
                    'last_20_trades': deque(maxlen=20),
                    'consecutive_losses': 0,
                    'is_active': True,
                    'cooldown_until': 0  # таймер отключения
                }
            logger.info(f"[LEARNER] Initialized {coin} with {strategies}")
    
    def register_trade(self, coin, strategy_name, pnl, timestamp):
        """егистрирует сделку и обновляет статистику"""
        if coin not in self.strategy_stats:
            return
        
        if strategy_name not in self.strategy_stats[coin]:
            return
        
        stats = self.strategy_stats[coin][strategy_name]
        
        # бновляем статистику
        if pnl > 0:
            stats['wins'] += 1
            stats['consecutive_losses'] = 0
        else:
            stats['losses'] += 1
            stats['consecutive_losses'] += 1
        
        stats['total_pnl'] += pnl
        stats['last_20_trades'].append({'pnl': pnl, 'timestamp': timestamp})
        
        # роверяем, нужно ли отключить стратегию
        self._evaluate_strategy(coin, strategy_name, timestamp)
        
        # огируем результат
        winrate = self.get_winrate(coin, strategy_name)
        logger.info(f"[LEARNER] {coin} {strategy_name}: winrate={winrate:.1f}%, active={stats['is_active']}")
    
    def _evaluate_strategy(self, coin, strategy_name, timestamp):
        """ценивает стратегию и отключает если плохая"""
        stats = self.strategy_stats[coin][strategy_name]
        
        # олучаем winrate за последние 20 сделок
        recent_trades = list(stats['last_20_trades'])
        if len(recent_trades) < self.min_trades:
            return  # недостаточно данных
        
        wins_recent = len([t for t in recent_trades if t['pnl'] > 0])
        winrate = wins_recent / len(recent_trades)
        
        # словия для отключения стратегии
        should_disable = False
        reason = ""
        
        # 1. изкий winrate
        if winrate < self.min_winrate:
            should_disable = True
            reason = f"winrate {winrate:.1%} < {self.min_winrate:.0%}"
        
        # 2. 3 убытка подряд
        elif stats['consecutive_losses'] >= self.max_consecutive_losses:
            should_disable = True
            reason = f"{stats['consecutive_losses']} consecutive losses"
        
        # 3. Сильно убыточная (общий PnL сильно отрицательный)
        elif len(recent_trades) >= 15 and stats['total_pnl'] < -50:
            should_disable = True
            reason = f"total PnL {stats['total_pnl']:.1f} < -50"
        
        if should_disable and stats['is_active']:
            # тключаем стратегию на 2 часа
            stats['is_active'] = False
            stats['cooldown_until'] = timestamp + 7200  # 2 часа в секундах
            logger.warning(f"[LEARNER] {coin} {strategy_name} DISABLED: {reason}")
    
    def get_active_strategy(self, coin, strategies, current_time):
        """озвращает лучшую активную стратегию для монеты"""
        if coin not in self.strategy_stats:
            self.init_coin(coin, strategies)
            return strategies[0]  # возвращаем первую
        
        # роверяем, не истек ли кулдаун у отключённых
        for strategy in strategies:
            if strategy in self.strategy_stats[coin]:
                stats = self.strategy_stats[coin][strategy]
                if not stats['is_active'] and current_time > stats['cooldown_until']:
                    # улдаун истёк — пробуем снова
                    stats['is_active'] = True
                    logger.info(f"[LEARNER] {coin} {strategy} REACTIVATED after cooldown")
        
        # Собираем активные стратегии
        active = []
        for strategy in strategies:
            if strategy in self.strategy_stats[coin]:
                if self.strategy_stats[coin][strategy]['is_active']:
                    active.append(strategy)
        
        if not active:
            # се стратегии отключены — включаем первую с малой долей
            logger.warning(f"[LEARNER] {coin} ALL strategies disabled, re-enabling first")
            self.strategy_stats[coin][strategies[0]]['is_active'] = True
            return strategies[0]
        
        # з активных выбираем лучшую по winrate
        best = None
        best_winrate = -1
        
        for strategy in active:
            winrate = self.get_winrate(coin, strategy)
            if winrate > best_winrate:
                best_winrate = winrate
                best = strategy
        
        return best
    
    def get_winrate(self, coin, strategy_name):
        """озвращает winrate стратегии за последние 20 сделок"""
        if coin not in self.strategy_stats:
            return 0.5
        
        if strategy_name not in self.strategy_stats[coin]:
            return 0.5
        
        stats = self.strategy_stats[coin][strategy_name]
        recent = list(stats['last_20_trades'])
        
        if len(recent) < 5:
            return 0.5  # недостаточно данных
        
        wins = len([t for t in recent if t['pnl'] > 0])
        return wins / len(recent)
    
    def get_summary(self, coin):
        """озвращает сводку по стратегиям монеты"""
        if coin not in self.strategy_stats:
            return {}
        
        summary = {}
        for strategy, stats in self.strategy_stats[coin].items():
            winrate = self.get_winrate(coin, strategy)
            summary[strategy] = {
                'active': stats['is_active'],
                'winrate': f"{winrate:.1%}",
                'trades': len(stats['last_20_trades']),
                'total_pnl': stats['total_pnl']
            }
        return summary
