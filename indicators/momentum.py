#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# indicators/momentum.py

def rsi(prices, period=14):
    """
    Рассчитывает классический индекс относительной силы (RSI) по методу Уайлдера.
    Работает по всей длине переданного массива для правильного сглаживания.
    """
    if len(prices) < period + 1:
        return 50.0
    
    # 1. Считаем все ценовые изменения (deltas) по порядку
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0.0 for d in deltas]
    losses = [-d if d < 0 else 0.0 for d in deltas]

    # 2. Базовое среднее для первой точки окна
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # 3. Скользящее сглаживание Уайлдера (RMA) по всей оставшейся истории
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def calculate_stochastic(prices, period=14):
    """
    Рассчитывает быстрый Стохастический Осциллятор (%K).
    Возвращает значение от 0 до 100.
    """
    if len(prices) < period:
        return 50.0
        
    recent = prices[-period:]
    low_min = min(recent)
    high_max = max(recent)
    
    if high_max == low_min:
        return 50.0
        
    return ((prices[-1] - low_min) / (high_max - low_min)) * 100.0