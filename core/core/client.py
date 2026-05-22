#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# core/client.py - лиент для работы с Pionex через прямой API

import os
import numpy as np
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from core.logger import logger
from core.api import get_price as api_get_price

load_dotenv()


class PionexClient:
    def __init__(self):
        self.api_key = os.getenv("PIONEX_API_KEY")
        self.api_secret = os.getenv("PIONEX_API_SECRET")
        
        if not self.api_key or not self.api_secret or self.api_key == "СТЬ_Ы_API_KEY":
            logger.warning("⚠️ API ключи не найдены! абота в  режиме.")
            self.paper_mode = True
        else:
            self.paper_mode = False
            logger.info("✅ Pionex клиент инициализирован (реальный режим через прямой API)")
    
    def get_balance(self, currency="USDT"):
        if self.paper_mode:
            return 1000.0
        logger.warning("еальный баланс ещё не реализован, используем бумажный")
        return 1000.0
    
    def get_price(self, symbol="BTC_USDT"):
        symbol_api = symbol.replace("/", "_")
        price = api_get_price(symbol_api)
        return price
    
    def market_buy(self, symbol, amount_usdt):
        price = self.get_price(symbol)
        if self.paper_mode:
            logger.info(f"[PAPER] BUY {amount_usdt:.2f} USDT of {symbol} @ {price}")
            return {"status": "FILLED", "price": price, "amount": amount_usdt / price if price else 0}
        logger.warning("еальная покупка ещё не реализована")
        return None
    
    def market_sell(self, symbol, amount):
        price = self.get_price(symbol)
        if self.paper_mode:
            logger.info(f"[PAPER] SELL {amount:.6f} of {symbol} @ {price}")
            return {"status": "FILLED", "price": price, "amount": amount}
        logger.warning("еальная продажа ещё не реализована")
        return None
    
    def get_ticker(self, symbol="BTC_USDT"):
        price = self.get_price(symbol)
        if price:
            return {"last": price, "symbol": symbol}
        return None

    def get_klines(self, symbol, interval="1h", limit=200):
        """олучает исторические свечи (бумажный режим — генерация, реальный — заглушка)"""
        if self.paper_mode:
            base_price = {
                "BTCUSDT": 50000,
                "BNBUSDT": 600,
                "XRPUSDT": 0.5,
                "ETHUSDT": 3000,
                "SOLUSDT": 150
            }.get(symbol, 100)
            changes = np.random.randn(limit) * 0.005
            prices = base_price * (1 + np.cumsum(changes))
            closes = prices.tolist()
            timestamps = [datetime.now() - pd.Timedelta(minutes=i*60) for i in range(limit)]
            closes = closes[::-1]
            timestamps = timestamps[::-1]
            return pd.DataFrame({"timestamp": timestamps, "close": closes})
        else:
            logger.error("еальная загрузка свечей через Pionex пока не реализована, используйте бумажный режим")
            return pd.DataFrame()


client = PionexClient()
