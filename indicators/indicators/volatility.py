#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# indicators/volatility.py

def calculate_bollinger_bandwidth(prices, period=20, num_std=2):
    """Рассчитывает ширину канала Боллинджера в процентах."""
    if len(prices) < period: 
        return 0.0
    recent = prices[-period:]
    sma = sum(recent) / period
    variance = sum((x - sma) ** 2 for x in recent) / period
    std_dev = variance ** 0.5
    upper_band = sma + (num_std * std_dev)
    lower_band = sma - (num_std * std_dev)
    if sma == 0: 
        return 0.0
    return ((upper_band - lower_band) / sma) * 100

def calculate_atr(prices, period=14):
    """
    Рассчитывает средний истинный диапазон (ATR) на основе цен закрытия.
    Возвращает среднюю волатильность текущего шума в процентах.
    """
    if len(prices) < period + 1:
        return 0.45  # Базовый шум рынка по умолчанию
    
    changes = [abs(prices[i] - prices[i-1]) / prices[i-1] * 100 for i in range(-period, 0)]
    return sum(changes) / period