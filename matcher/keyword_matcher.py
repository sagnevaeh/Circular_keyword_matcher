# ============================================================
# matcher/keyword_matcher.py
# Matches keywords against real NSE API field names.
# Supports both default keywords and custom search keywords.
# ============================================================

import logging
from config.keywords import KEYWORDS

logger = logging.getLogger(__name__)


def find_matches(circulars: list[dict], custom_keywords: list[str] = None) -> list[dict]:
    """
    Scans each circular for keyword matches.

    Args:
        circulars        : List of circular dicts from NSE API.
        custom_keywords  : Optional custom keyword list (overrides config).

    Returns:
        List of matched circulars with 'matched_keywords' key added.
    """
    keywords   = custom_keywords if custom_keywords else KEYWORDS
    kws_lower  = [kw.lower() for kw in keywords]
    matched    = []
    seen_nos   = set()

    for circular in circulars:
        subject    = circular.get("sub", "") or ""
        dept       = circular.get("circDepartment", "") or ""
        dept_short = circular.get("fileDept", "") or ""
        circ_no    = circular.get("circDisplayNo", "") or ""

        # Deduplicate same circular appearing across multiple dept rows
        if circ_no and circ_no in seen_nos:
            continue
        seen_nos.add(circ_no)

        search_text = f"{subject} {dept} {dept_short} {circ_no}".lower()

        hits = [kw for kw, kw_lower in zip(keywords, kws_lower)
                if kw_lower in search_text]

        if hits:
            result = dict(circular)
            result["matched_keywords"] = hits
            matched.append(result)
            logger.info(f"  ✅ MATCH [{circ_no}] → {hits}")

    logger.info(f"Matched {len(matched)} / {len(seen_nos)} unique circulars.")
    return matched