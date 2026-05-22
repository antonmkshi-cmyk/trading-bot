def calculate_rsi(prices, period=14):
    """
    Рассчитывает классический RSI (относительную силу) по методу Уайлдера.
    Защищен от деления на ноль и динамической длины истории.
    """
    if not prices or len(prices) <= period:
        return None

    # Нам нужны только последние свечи для расчета (период + 1 для получения изменений)
    # Но для сглаживания Уайлдера лучше брать чуть больше истории, если она есть
    # Ограничим срез, чтобы не пересчитывать тысячи свечей каждый раз
    max_history = period * 5
    recent_prices = prices[-max_history:]
    
    gains = []
    losses = []
    
    # Считаем первичные изменения цен
    for i in range(1, len(recent_prices)):
        change = recent_prices[i] - recent_prices[i - 1]
        if change > 0:
            gains.append(change)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(change))
            
    # Если изменений набралось меньше, чем период — данных не хватает
    if len(gains) < period:
        return None

    # Считаем первое простое среднее (SMA) за самый первый период
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # Применяем сглаживание Уайлдера (RMA) для оставшихся изменений
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    # Защита от деления на ноль (если цена стояла как вкопанная)
    if avg_loss == 0:
        if avg_gain == 0:
            return 50.0  # Цена не менялась, RSI ровно посередине
        return 100.0  # Цена только росла, падений не было вообще

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    
    return float(rsi)