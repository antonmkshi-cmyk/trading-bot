#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Market Context Object for Orchestra Engine.
Provides calibrated safety filters against NoneType errors in strategies.
"""

import logging
import math

logger = logging.getLogger("Orchestra.MarketContext")

class MarketContext:
    def __init__(self, closes_5m, volumes_5m, closes_15m, bb_width_15m):
        """
        Контекст рынка, собирающий данные для анализа ансамблем стратегий.
        Включена жесткая фильтрация NoneType для FLAT_SNIPER.
        """
        self.closes_5m = closes_5m if closes_5m is not None else []
        self.volumes_5m = volumes_5m if volumes_5m is not None else []
        self.closes_15m = closes_15m if closes_15m is not None else []
        
        # Жесткая защита от NoneType для ширины полосы Боллинджера (основной триггер Снайпера)
        if bb_width_15m is None or (isinstance(bb_width_15m, float) and math.isnan(bb_width_15m)):
            self.bb_width_15m = 0.02  # Безопасное нейтральное значение (канал 2%)
        else:
            try:
                self.bb_width_15m = float(bb_width_15m)
            except (ValueError, TypeError):
                self.bb_width_15m = 0.02

        # Дополнительная валидация
        self.is_valid = self._validate_context()

    def _validate_context(self):
        """Проверяет, достаточно ли данных для безопасного анализа"""
        if not self.closes_5m or not self.closes_15m:
            return False
        if len(self.closes_5m) < 20:
            return False
        return True