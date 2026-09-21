# ============================================================
# logger/log_writer.py
# Maps ALL real NSE API fields exactly to log output.
# ============================================================

import os
import logging
from datetime import datetime

logger   = logging.getLogger(__name__)
LOGS_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")


def write_log(matched_circulars: list[dict],
              from_date: str = None,
              to_date: str = None,
              keywords_used: list[str] = None) -> str:

    os.makedirs(LOGS_DIR, exist_ok=True)

    today    = datetime.now().strftime("%Y-%m-%d")
    run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_path = os.path.join(LOGS_DIR, f"nse_circulars_{today}.log")

    with open(log_path, "a", encoding="utf-8") as f:

        # ── Header ──────────────────────────────────────────
        f.write("=" * 70 + "\n")
        f.write(f"  NSE CIRCULAR KEYWORD MONITOR — Run at {run_time}\n")
        if from_date and to_date:
            f.write(f"  Date Range  : {from_date}  →  {to_date}\n")
        if keywords_used:
            f.write(f"  Keywords    : {', '.join(keywords_used)}\n")
        f.write("=" * 70 + "\n\n")

        if not matched_circulars:
            f.write("  No circulars matched the keywords in this run.\n\n")
            f.write("=" * 70 + "\n")
            logger.info("No matches — wrote note to log.")
            return log_path

        f.write(f"  🔔 {len(matched_circulars)} MATCHED CIRCULAR(S) FOUND\n\n")

        for idx, circ in enumerate(matched_circulars, start=1):
            kws = circ.get("matched_keywords", [])

            # ── Every field from real NSE API ────────────────
            f.write(f"  [{idx}] " + "-" * 60 + "\n")
            f.write(f"      Date        : {circ.get('cirDisplayDate', 'N/A')}\n")
            f.write(f"      Circular No : {circ.get('circDisplayNo',  'N/A')}\n")
            f.write(f"      Company     : {circ.get('circCompany',    'N/A')}\n")
            f.write(f"      Department  : {circ.get('circDepartment', 'N/A')}\n")
            f.write(f"      Dept Code   : {circ.get('fileDept',       'N/A')}\n")
            f.write(f"      Category    : {circ.get('circCategory',   'N/A')}\n")
            f.write(f"      Subject     : {circ.get('sub',            'N/A')}\n")
            f.write(f"      File Size   : {circ.get('circFileSize',   'N/A')}\n")
            f.write(f"      File Type   : {circ.get('fileExt',        'N/A').upper()}\n")
            f.write(f"      PDF Link    : {circ.get('circFilelink',   'N/A')}\n")
            f.write(f"      Matched By  : {' | '.join(f'\"{k}\"' for k in kws)}\n")
            f.write("\n")

        f.write("=" * 70 + "\n")

    logger.info(f"Log written → {log_path}")
    return log_path