# ============================================================
# fetcher/circulars.py
# Fetches ALL circulars using pagination across full date range
# ============================================================

import logging
import time
import gzip
import json
from datetime import datetime, timedelta
from fetcher.session import create_nse_session

logger = logging.getLogger(__name__)

BASE_URL   = "https://www.nseindia.com/api/circulars"
LATEST_URL = "https://www.nseindia.com/api/latest-circular"


def safe_parse(resp) -> dict | list | None:
    raw = resp.content
    if not raw:
        logger.warning("  Empty response body.")
        return None

    # Brotli
    try:
        import brotli
        text = brotli.decompress(raw).decode("utf-8")
        logger.info(f"  ✅ Brotli OK. Preview: {text[:80]}")
        return json.loads(text)
    except ImportError:
        pass
    except Exception as e:
        logger.info(f"  Brotli failed: {e}")

    # Gzip
    try:
        if raw[:2] == b'\x1f\x8b':
            text = gzip.decompress(raw).decode("utf-8")
            logger.info(f"  ✅ Gzip OK. Preview: {text[:80]}")
            return json.loads(text)
    except Exception as e:
        logger.info(f"  Gzip failed: {e}")

    # requests built-in
    try:
        text = resp.text
        if text and not text.strip().startswith("<"):
            return json.loads(text)
    except Exception as e:
        logger.info(f"  resp.text failed: {e}")

    # Plain
    try:
        text = raw.decode("utf-8", errors="ignore")
        if text.strip().startswith(("{", "[")):
            return json.loads(text)
        if text.strip().startswith("<"):
            logger.warning("  Got HTML — session blocked.")
            return None
    except Exception as e:
        logger.error(f"  Plain decode failed: {e}")

    logger.error("  ❌ All decode attempts failed.")
    return None


def fetch_page(session, from_date: str, to_date: str,
               dept: str = None, page: int = 1) -> dict | None:
    """
    Fetch a single page of circulars from NSE API.

    NSE API params:
        from_date  : DD-MM-YYYY
        to_date    : DD-MM-YYYY
        dept       : dept code filter e.g. "MSD", "CML" (optional)
        page_no    : page number (1-based)
    """
    params = f"from_date={from_date}&to_date={to_date}&page_no={page}"
    if dept:
        params += f"&dept={dept}"

    url = f"{BASE_URL}?{params}"
    logger.info(f"  Fetching page {page}: {url}")

    try:
        resp = session.get(url, timeout=20)
        logger.info(f"    Status: {resp.status_code} | Size: {len(resp.content)} bytes")
        if resp.status_code == 200 and resp.content:
            return safe_parse(resp)
    except Exception as e:
        logger.error(f"    Page {page} fetch error: {e}")

    return None


def fetch_circulars(from_date: str = None, to_date: str = None) -> list[dict]:
    """
    Fetches ALL circulars from NSE for a given date range
    by iterating through all available pages.

    Args:
        from_date : "DD-MM-YYYY"  (default: 7 days ago)
        to_date   : "DD-MM-YYYY"  (default: today)

    Returns:
        Deduplicated list of all circular dicts in the range.
    """
    if not to_date:
        to_date   = datetime.now().strftime("%d-%m-%Y")
    if not from_date:
        from_date = (datetime.now() - timedelta(days=7)).strftime("%d-%m-%Y")

    logger.info(f"Fetching ALL circulars: {from_date} → {to_date}")

    session    = create_nse_session()
    all_circulars = []
    seen_nos   = set()

    # ── Page through all results ────────────────────────────
    page = 1
    while True:
        time.sleep(1)  # be polite to NSE
        data = fetch_page(session, from_date, to_date, page=page)

        if not data:
            logger.info(f"  No data on page {page} — stopping.")
            break

        # NSE wraps in "data" key
        records = data.get("data", []) if isinstance(data, dict) else data

        if not records:
            logger.info(f"  Empty records on page {page} — stopping.")
            break

        # Deduplicate by circular number
        new_count = 0
        for circ in records:
            circ_no = circ.get("circDisplayNo", "") or circ.get("circNumber", "")
            dept    = circ.get("fileDept", "")
            key     = f"{circ_no}_{dept}"   # dept makes it unique per row
            if key not in seen_nos:
                seen_nos.add(key)
                all_circulars.append(circ)
                new_count += 1

        logger.info(f"  Page {page}: {len(records)} records, {new_count} new. Total so far: {len(all_circulars)}")

        # Check if more pages exist
        total_records = data.get("total", None) if isinstance(data, dict) else None
        page_size     = data.get("pageSize", len(records)) if isinstance(data, dict) else len(records)

        if total_records:
            fetched_so_far = page * (page_size or 10)
            logger.info(f"  Total available: {total_records} | Fetched: {fetched_so_far}")
            if fetched_so_far >= int(total_records):
                logger.info("  All pages fetched.")
                break
        else:
            # No total info — stop if we got fewer records than a full page
            # or if this page returned no new records
            if new_count == 0 or len(records) < 10:
                logger.info("  Reached last page.")
                break

        page += 1

        # Safety cap — avoid infinite loop
        if page > 50:
            logger.warning("  Reached 50 page limit — stopping.")
            break

    # ── Fallback if pagination gave nothing ─────────────────
    if not all_circulars:
        logger.warning("Pagination returned nothing. Trying direct endpoints...")
        for url in [f"{BASE_URL}?from_date={from_date}&to_date={to_date}",
                    BASE_URL, LATEST_URL]:
            try:
                time.sleep(1)
                resp = session.get(url, timeout=20)
                if resp.status_code == 200:
                    data = safe_parse(resp)
                    if data:
                        records = data.get("data", []) if isinstance(data, dict) else data
                        all_circulars.extend(records)
                        logger.info(f"  Fallback got {len(records)} records from {url}")
                        break
            except Exception as e:
                logger.error(f"  Fallback {url} failed: {e}")

    logger.info(f"\n✅ Total circulars fetched: {len(all_circulars)}")
    return all_circulars