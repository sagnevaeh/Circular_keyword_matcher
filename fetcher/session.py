# ============================================================
# fetcher/session.py
# ============================================================

import requests
import time
import logging

logger = logging.getLogger(__name__)

PAGE_HEADERS = {
    "User-Agent":                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept":                    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language":           "en-US,en;q=0.9",
    "Accept-Encoding":           "gzip, deflate",   # NO brotli here — forces gzip which requests handles natively
    "Connection":                "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest":            "document",
    "Sec-Fetch-Mode":            "navigate",
    "Sec-Fetch-Site":            "none",
    "Sec-Fetch-User":            "?1",
    "Cache-Control":             "max-age=0",
}

API_HEADERS = {
    "User-Agent":       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept":           "application/json, text/plain, */*",
    "Accept-Language":  "en-US,en;q=0.9",
    "Accept-Encoding":  "gzip, deflate",   # NO brotli — so requests auto-decompresses
    "Referer":          "https://www.nseindia.com/regulations/circulars",
    "X-Requested-With": "XMLHttpRequest",
    "Sec-Fetch-Dest":   "empty",
    "Sec-Fetch-Mode":   "cors",
    "Sec-Fetch-Site":   "same-origin",
    "Connection":       "keep-alive",
}


def create_nse_session() -> requests.Session:
    """
    KEY FIX: Accept-Encoding = 'gzip, deflate' (NOT brotli).
    This forces NSE to respond with gzip which requests
    decompresses automatically — no brotli library needed.
    """
    session = requests.Session()

    try:
        logger.info("Step 1: Visiting NSE homepage...")
        session.headers.update(PAGE_HEADERS)
        r1 = session.get("https://www.nseindia.com", timeout=20)
        logger.info(f"  Homepage status: {r1.status_code} | Cookies: {list(session.cookies.keys())}")
        time.sleep(3)

        logger.info("Step 2: Visiting circulars page...")
        session.headers.update({"Referer": "https://www.nseindia.com/"})
        r2 = session.get("https://www.nseindia.com/regulations/circulars", timeout=20)
        logger.info(f"  Circulars page status: {r2.status_code} | Cookies: {list(session.cookies.keys())}")
        time.sleep(3)

        # Switch to API headers for all subsequent calls
        session.headers.update(API_HEADERS)

        logger.info("Session ready ✅")
        return session

    except requests.exceptions.RequestException as e:
        logger.error(f"Session creation failed: {e}")
        raise