#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# core/api.py - API запросы к Pionex с retry-логикой

import time
import requests
from core.logger import logger

try:
    from config import BASE_URL, REQUEST_TIMEOUT
except ImportError:
    BASE_URL = "https://api.pionex.com"
    REQUEST_TIMEOUT = 10


def request_with_retry(url, params=None, max_retries=5, timeout=REQUEST_TIMEOUT):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            if response.status_code == 200:
                return response
            logger.warning(f"Bad status code: {response.status_code}, attempt {attempt + 1}/{max_retries}")
        except requests.Timeout:
            logger.warning(f"Timeout error, attempt {attempt + 1}/{max_retries}")
        except Exception as e:
            logger.warning(f"Request error: {e}, attempt {attempt + 1}/{max_retries}")
        
        if attempt < max_retries - 1:
            wait = 2 ** attempt
            logger.info(f"Waiting {wait} seconds before retry...")
            time.sleep(wait)
    
    logger.error(f"Failed after {max_retries} attempts")
    return None


def get_symbols():
    url = f"{BASE_URL}/api/v1/common/symbols"
    logger.info("Requesting trading symbols...")
    response = request_with_retry(url)
    if response is None:
        return None
    try:
        data = response.json()
        if not data.get("data"):
            logger.error("Invalid API response structure")
            return None
        symbols = data["data"]["symbols"]
        logger.info(f"Loaded {len(symbols)} symbols")
        return symbols
    except Exception as e:
        logger.error(f"JSON parsing error: {e}")
        return None


def get_price(symbol, max_retries=3):
    url = f"{BASE_URL}/api/v1/market/tickers"
    logger.info(f"Requesting price for {symbol}")
    for attempt in range(max_retries):
        response = request_with_retry(url, max_retries=1)
        if response is None:
            if attempt < max_retries - 1:
                logger.info(f"Retrying price request ({attempt + 2}/{max_retries})...")
                time.sleep(2)
            continue
        try:
            data = response.json()
            if not data.get("data"):
                logger.error("Invalid ticker response")
                continue
            tickers = data["data"]["tickers"]
            for ticker in tickers:
                if ticker["symbol"] == symbol:
                    price = float(ticker["close"])
                    logger.info(f"{symbol} price: {price}")
                    return price
            logger.warning(f"{symbol} not found in tickers")
            return None
        except Exception as e:
            logger.error(f"Error parsing price response: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            continue
    logger.error(f"Failed to get price for {symbol} after {max_retries} attempts")
    return None
