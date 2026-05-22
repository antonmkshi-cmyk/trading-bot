# indicators/levels.py
"""
УРОВНИ ПОДДЕРЖКИ И СОПРОТИВЛЕНИЯ
"""

def support_resistance(prices, window=40):
    """
    Находит уровни поддержки и сопротивления
    Возвращает (support, resistance)
    """
    if len(prices) < window:
        return None, None
    
    recent = prices[-window:]
    lows, highs = [], []
    
    for i in range(1, len(recent) - 1):
        # Локальный минимум
        if recent[i] < recent[i-1] and recent[i] < recent[i+1]:
            lows.append(recent[i])
        # Локальный максимум
        if recent[i] > recent[i-1] and recent[i] > recent[i+1]:
            highs.append(recent[i])
    
    if not lows or not highs:
        return None, None
    
    return sum(lows) / len(lows), sum(highs) / len(highs)


def is_near_level(price, level, tolerance=0.05):
    """
    Проверяет, находится ли цена у уровня
    tolerance — допустимое отклонение в процентах
    """
    if level is None or level == 0:
        return False
    return abs(price - level) / level * 100 <= tolerance