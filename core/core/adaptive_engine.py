#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# core/adaptive_engine.py - Самообучающийся адаптивный движок

import numpy as np
from collections import deque
from core.logger import logger


class AdaptiveEngine:
    """Самообучающийся движок для адаптации к рынку"""
    
    def __init__(self, history_size=100):
        self.history_size = history_size
        self.trade_history = deque(maxlen=history_size)
        self.performance_by_regime = {
            'trend_high': {'wins': 0, 'losses': 0, 'total_pnl': 0, 'trades': []},
            'trend_low': {'wins': 0, 'losses': 0, 'total_pnl': 0, 'trades': []},
            'sideways_high': {'wins': 0, 'losses': 0, 'total_pnl': 0, 'trades': []},
            'sideways_low': {'wins': 0, 'losses': 0, 'total_pnl': 0, 'trades': []},
        }
        
        # араметры, которые будем адаптировать
        self.adaptive_params = {
            'entry_threshold': 50.0,
            'tp_percent': 0.8,
            'sl_percent': 1.2,
            'trailing_stop_pct': 0.8,
            'min_volatility': 0.008,
            'max_position_usdt': 150,
        }
        
        self.regime_history = deque(maxlen=50)
        self.last_regime = 'sideways_low'
        self.learning_rate = 0.1
        
        logger.info("=== ADAPTIVE ENGINE INITIALIZED ===")
    
    def detect_market_regime(self, adx_value, volatility_pct):
        """пределяет режим рынка на основе ADX и волатильности"""
        if adx_value > 35:
            trend = 'trend'
        elif adx_value < 22:
            trend = 'sideways'
        else:
            trend = 'transition'
        
        if volatility_pct > 0.5:
            vol = 'high'
        elif volatility_pct < 0.2:
            vol = 'low'
        else:
            vol = 'medium'
        
        if trend == 'trend' and vol == 'high':
            regime = 'trend_high'
        elif trend == 'trend':
            regime = 'trend_low'
        elif trend == 'sideways' and vol == 'high':
            regime = 'sideways_high'
        else:
            regime = 'sideways_low'
        
        self.regime_history.append(regime)
        self.last_regime = regime
        return regime
    
    def update_after_trade(self, trade):
        """бновляет статистику после сделки и адаптирует параметры"""
        self.trade_history.append(trade)
        regime = trade.get('regime', self.last_regime)
        
        if regime in self.performance_by_regime:
            perf = self.performance_by_regime[regime]
            perf['trades'].append(trade)
            if trade['pnl'] > 0:
                perf['wins'] += 1
            else:
                perf['losses'] += 1
            perf['total_pnl'] += trade['pnl']
            
            # ставляем только последние 50 сделок
            if len(perf['trades']) > 50:
                oldest = perf['trades'].pop(0)
                if oldest['pnl'] > 0:
                    perf['wins'] -= 1
                else:
                    perf['losses'] -= 1
                perf['total_pnl'] -= oldest['pnl']
        
        # даптируем параметры
        self._adapt_parameters()
    
    def _adapt_parameters(self):
        """даптирует параметры бота под текущие рыночные условия"""
        if len(self.trade_history) < 20:
            return
        
        recent_trades = list(self.trade_history)[-20:]
        wins = [t for t in recent_trades if t['pnl'] > 0]
        losses = [t for t in recent_trades if t['pnl'] < 0]
        winrate = len(wins) / len(recent_trades) if recent_trades else 0.5
        
        # олучаем статистику по текущему режиму
        regime_perf = self.performance_by_regime.get(self.last_regime, {})
        regime_trades = regime_perf.get('trades', [])
        regime_wins = regime_perf.get('wins', 0)
        regime_total = len(regime_trades)
        regime_winrate = regime_wins / regime_total if regime_total > 0 else 0.5
        
        # даптация порога входа
        if winrate < 0.4:
            # быточная серия — повышаем порог (входим реже)
            self.adaptive_params['entry_threshold'] = min(80, self.adaptive_params['entry_threshold'] + 5)
            logger.info(f"[ADAPT] Winrate low ({winrate:.2f}), raising entry threshold to {self.adaptive_params['entry_threshold']:.0f}")
        elif winrate > 0.6:
            # рибыльная серия — снижаем порог (входим чаще)
            self.adaptive_params['entry_threshold'] = max(30, self.adaptive_params['entry_threshold'] - 5)
            logger.info(f"[ADAPT] Winrate high ({winrate:.2f}), lowering entry threshold to {self.adaptive_params['entry_threshold']:.0f}")
        
        # даптация TP/SL под режим рынка
        if self.last_regime == 'trend_high':
            # Сильный тренд — увеличиваем TP, оставляем SL
            self.adaptive_params['tp_percent'] = min(1.5, self.adaptive_params['tp_percent'] + 0.05)
            logger.info(f"[ADAPT] Strong trend, TP increased to {self.adaptive_params['tp_percent']:.2f}%")
        elif self.last_regime == 'sideways_low':
            # лэт — уменьшаем TP (быстрый выход)
            self.adaptive_params['tp_percent'] = max(0.4, self.adaptive_params['tp_percent'] - 0.05)
            logger.info(f"[ADAPT] Low volatility, TP decreased to {self.adaptive_params['tp_percent']:.2f}%")
        
        # даптация размера позиции под уверенность
        confidence = regime_winrate if regime_total > 10 else 0.5
        base_size = 150
        self.adaptive_params['max_position_usdt'] = max(50, min(300, base_size * confidence * 2))
    
    def get_adaptive_entry_threshold(self):
        """озвращает адаптивный порог входа"""
        return self.adaptive_params['entry_threshold']
    
    def get_adaptive_tp_sl(self):
        """озвращает адаптивные TP/SL"""
        return self.adaptive_params['tp_percent'], self.adaptive_params['sl_percent']
    
    def should_adapt_strategy_weights(self):
        """пределяет, нужно ли пересмотреть веса стратегий"""
        if len(self.trade_history) < 20:
            return False
        
        # сли winrate падает ниже 35% на дистанции 20 сделок
        recent = list(self.trade_history)[-20:]
        wins = len([t for t in recent if t['pnl'] > 0])
        winrate = wins / 20
        
        return winrate < 0.35
    
    def get_strategy_performance_summary(self):
        """озвращает сводку по эффективности стратегий в разных режимах"""
        summary = {}
        for regime, perf in self.performance_by_regime.items():
            total = len(perf['trades'])
            if total > 0:
                summary[regime] = {
                    'winrate': perf['wins'] / total,
                    'total_pnl': perf['total_pnl'],
                    'trades': total
                }
        return summary
    
    def reset_for_new_coin(self, coin_name):
        """Сбрасывает статистику для новой монеты (разные монеты — разная динамика)"""
        # Создаём копию структуры для монеты
        self.coin_performance = getattr(self, 'coin_performance', {})
        self.coin_performance[coin_name] = {
            'trade_history': deque(maxlen=self.history_size),
            'performance_by_regime': {
                'trend_high': {'wins': 0, 'losses': 0, 'total_pnl': 0},
                'trend_low': {'wins': 0, 'losses': 0, 'total_pnl': 0},
                'sideways_high': {'wins': 0, 'losses': 0, 'total_pnl': 0},
                'sideways_low': {'wins': 0, 'losses': 0, 'total_pnl': 0},
            }
        }
        logger.info(f"[ADAPT] Reset stats for {coin_name}")
