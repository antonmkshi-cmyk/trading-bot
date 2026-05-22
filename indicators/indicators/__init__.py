#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# indicators/__init__.py

from .trend import calculate_sma, calculate_adx
from .momentum import rsi, calculate_stochastic
from .volatility import calculate_bollinger_bandwidth, calculate_atr

# Удобные псевдонимы для импорта
sma = calculate_sma
adx = calculate_adx
stoch = calculate_stochastic
bollinger_bandwidth = calculate_bollinger_bandwidth
atr = calculate_atr