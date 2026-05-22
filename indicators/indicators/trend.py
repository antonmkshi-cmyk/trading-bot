#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# indicators/trend.py

def calculate_sma(prices, period=20):
    """Рассчитывает простую скользящую среднюю (SMA)."""
    if len(prices) < period:
        return prices[-1] if prices else 0.0
    return sum(prices[-period:]) / period

def calculate_adx(prices, period=14):
    """Упрощенный расчет силы тренда на основе разницы цен."""
    if len(prices) < period + 1:
        return 20.0
    
    changes = []
    for i in range(1, period + 1):
        changes.append(abs(prices[-i] - prices[-i-1]))
        
    avg_change = sum(changes) / period
    if prices[-1] == 0: return 20.0
    
    adx_value = (avg_change / prices[-1]) * 10000
    return min(100.0, max(0.0, adx_value))