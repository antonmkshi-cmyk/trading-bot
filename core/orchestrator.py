#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# core/orchestrator.py - Quantum Orchestrator с PnL-обучением

import math
import json
import os
import config
from strategies.sniper_mtf import SniperMTFStrategy
from strategies.trend_follower import TrendFollowerStrategy
from strategies.trend_sniper import TrendSniperStrategy

class QuantumOrchestrator:
    def __init__(self):
        self.portfolio = {
            "TREND_SNIPER":     {"instance": TrendSniperStrategy(),    "weight": 0.4},
            "FLAT_SNIPER": {
                "instance": SniperMTFStrategy(),
                "weight": 0.5,
                "wins": 0,
                "losses": 0,
                "total_pnl": 0.0,
                "last_20_trades": []
            },
            "TREND_FOLLOWER": {
                "instance": TrendFollowerStrategy(),
                "weight": 0.5,
                "wins": 0,
                "losses": 0,
                "total_pnl": 0.0,
                "last_20_trades": []
            }
        }
        self.total_trades = 0
        self.performance_file = "strategy_performance.json"
        self._load_performance()
    
    def _load_performance(self):
        """агружает сохранённую статистику стратегий"""
        if os.path.exists(self.performance_file):
            try:
                with open(self.performance_file, 'r') as f:
                    data = json.load(f)
                    for name in self.portfolio:
                        if name in data:
                            self.portfolio[name]['wins'] = data[name].get('wins', 0)
                            self.portfolio[name]['losses'] = data[name].get('losses', 0)
                            self.portfolio[name]['total_pnl'] = data[name].get('total_pnl', 0.0)
                            self.portfolio[name]['last_20_trades'] = data[name].get('last_20_trades', [])
                print(f"[ORCHESTRA] Loaded performance data")
            except Exception as e:
                print(f"[ORCHESTRA] Could not load performance: {e}")
    
    def _save_performance(self):
        """Сохраняет статистику стратегий"""
        try:
            data = {}
            for name, strat in self.portfolio.items():
                data[name] = {
                    'wins': strat['wins'],
                    'losses': strat['losses'],
                    'total_pnl': strat['total_pnl'],
                    'last_20_trades': strat['last_20_trades'][-20:]  # храним только последние 20
                }
            with open(self.performance_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[ORCHESTRA] Could not save performance: {e}")
    
    def update_strategy_performance(self, strategy_name, pnl):
        """бновляет статистику стратегии после сделки и пересчитывает вес"""
        if strategy_name not in self.portfolio:
            return
        
        strat = self.portfolio[strategy_name]
        
        # бновляем статистику
        if pnl > 0:
            strat['wins'] += 1
        else:
            strat['losses'] += 1
        
        strat['total_pnl'] += pnl
        strat['last_20_trades'].append(pnl)
        if len(strat['last_20_trades']) > 20:
            strat['last_20_trades'].pop(0)
        
        # ересчитываем вес на основе winrate последних 20 сделок
        recent_trades = strat['last_20_trades']
        if len(recent_trades) >= 5:
            wins_recent = len([p for p in recent_trades if p > 0])
            winrate = wins_recent / len(recent_trades)
            
            # ормализованный PnL за последние 20 сделок (от -1 до 1)
            max_pnl = max(recent_trades) if recent_trades else 1
            min_pnl = min(recent_trades) if recent_trades else -1
            range_pnl = max_pnl - min_pnl if max_pnl != min_pnl else 1
            normalized_pnl = (strat['total_pnl'] / len(recent_trades) - min_pnl) / range_pnl if range_pnl > 0 else 0.5
            
            # овый вес = (winrate * 0.7) + (normalized_pnl * 0.3)
            new_weight = (winrate * 0.7) + (normalized_pnl * 0.3)
            new_weight = max(0.1, min(0.9, new_weight))  # граничиваем 0.1-0.9
            
            # лавное обновление (не резко)
            strat['weight'] = strat['weight'] * 0.7 + new_weight * 0.3
            
            print(f"[ORCHESTRA] {strategy_name}: winrate={winrate:.2f}, new_weight={strat['weight']:.2f}")
        
        self._save_performance()
    
    def _calculate_market_regime(self, context):
        if context is None or not hasattr(context, 'closes_5m') or len(context.closes_5m) < 50:
            return {"trend_strength": 20.0, "volatility_scalar": 1.0, "current_vol_pct": 0.2}

        current_price = context.closes_5m[-1]
        if current_price is None or current_price == 0:
            return {"trend_strength": 20.0, "volatility_scalar": 1.0, "current_vol_pct": 0.2}
        
        recent_ranges = [(max(context.closes_5m[i-14:i]) - min(context.closes_5m[i-14:i])) / context.closes_5m[i] for i in range(-30, 0)]
        avg_historical_vol = sum(recent_ranges) / len(recent_ranges) if recent_ranges else 0.002
        
        current_vol = (max(context.closes_5m[-14:]) - min(context.closes_5m[-14:])) / current_price
        volatility_scalar = current_vol / avg_historical_vol if avg_historical_vol > 0 else 1.0
        
        return {
            "volatility_scalar": max(0.5, min(volatility_scalar, 2.5)),
            "current_vol_pct": current_vol * 100
        }

    def get_ensemble_signal(self, market_context, trend_strength):
        if trend_strength is None or (isinstance(trend_strength, float) and math.isnan(trend_strength)):
            trend_strength = 20.0
            
        regime = self._calculate_market_regime(market_context)
        v_scalar = regime["volatility_scalar"]
        
        # инамические веса на основе ADX (рыночный режим)
        if trend_strength <= 22.0:
            adx_weight_sniper = 0.85
            adx_weight_trend = 0.15
        elif trend_strength >= 35.0:
            adx_weight_sniper = 0.10
            adx_weight_trend = 0.90
        else:
            adx_weight_sniper = 0.50
            adx_weight_trend = 0.50
        
        # тоговый вес = (ADX-вес * 0.6) + (PnL-вес * 0.4)
        final_weight_sniper = (adx_weight_sniper * 0.6) + (self.portfolio["FLAT_SNIPER"]["weight"] * 0.4)
        final_weight_trend = (adx_weight_trend * 0.6) + (self.portfolio["TREND_FOLLOWER"]["weight"] * 0.4)
        
        self.portfolio["FLAT_SNIPER"]["weight"] = final_weight_sniper
        self.portfolio["TREND_FOLLOWER"]["weight"] = final_weight_trend

        total_score = 0.0
        debug_info = []

        for bot_name, bot_config in self.portfolio.items():
            bot = bot_config["instance"]
            weight = bot_config["weight"]

            try:
                vote = bot.get_signal_score(market_context, v_scalar)
                if vote is None:
                    vote = 0.0
                weighted_vote = vote * weight
                total_score += weighted_vote
                if vote != 0:
                    debug_info.append(f"{bot_name}: {vote:+.1f} (w={weight:.2f}) -> {weighted_vote:+.1f}")
            except Exception as e:
                print(f"[ERROR] {bot_name}: {e}")

        if debug_info:
            print(f"[ORCHESTRA] ADX:{trend_strength:.1f} | SCORE:{total_score:+.2f}")

        if total_score >= config.ENTRY_THRESHOLD:
            return "LONG"
        elif total_score <= -config.ENTRY_THRESHOLD:
            return "SHORT"
            
        return "HOLD"

