# ============================================================
# main.py  —  NSE Circular Monitor
#
# TWO MODES:
#   1. Automated  : python main.py
#                   Uses default keywords + last 7 days
#
#   2. Interactive: python main.py --search
#                   Prompts for custom keywords + date range
# ============================================================

import logging
import sys
import argparse
from datetime import datetime, timedelta

# ── Logging setup ───────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s → %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("main")

from fetcher.circulars        import fetch_circulars
from matcher.keyword_matcher  import find_matches
from logger.log_writer        import write_log
from config.keywords          import KEYWORDS


# ── Helpers ─────────────────────────────────────────────────

def validate_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%d-%m-%Y")
        return True
    except ValueError:
        return False


def print_banner():
    print("\n" + "=" * 60)
    print("       NSE CIRCULAR KEYWORD MONITOR")
    print("=" * 60)


def print_results_to_screen(matched: list[dict], keywords: list[str],
                             from_date: str, to_date: str):
    """Pretty-print matched results directly to terminal."""
    print("\n" + "=" * 60)
    print(f"  SEARCH RESULTS")
    print(f"  Keywords   : {', '.join(keywords)}")
    print(f"  Date Range : {from_date}  →  {to_date}")
    print("=" * 60)

    if not matched:
        print("\n  ❌ No circulars matched your search.\n")
        return

    print(f"\n  ✅ {len(matched)} circular(s) found.\n")

    for idx, circ in enumerate(matched, start=1):
        kws = circ.get("matched_keywords", [])
        print(f"  [{idx}] " + "-" * 54)
        print(f"      Date        : {circ.get('cirDisplayDate', 'N/A')}")
        print(f"      Circular No : {circ.get('circDisplayNo',  'N/A')}")
        print(f"      Department  : {circ.get('circDepartment', 'N/A')}")
        print(f"      Category    : {circ.get('circCategory',   'N/A')}")
        print(f"      Subject     : {circ.get('sub',            'N/A')}")
        print(f"      PDF Link    : {circ.get('circFilelink',   'N/A')}")
        print(f"      Matched By  : {' | '.join(f'\"{k}\"' for k in kws)}")
        print()

    print("=" * 60)


# ── Mode 1: Automated (called by scheduler) ─────────────────

def run_automated():
    """Runs with default keywords + last 7 days. Called by scheduler."""
    logger.info("=" * 60)
    logger.info("  NSE Circular Monitor — AUTOMATED RUN")
    logger.info(f"  Time     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"  Keywords : {KEYWORDS}")
    logger.info("=" * 60)

    to_date   = datetime.now().strftime("%d-%m-%Y")
    from_date = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")

    logger.info("\n📡 STEP 1: Fetching circulars...")
    circulars = fetch_circulars(from_date=from_date, to_date=to_date)
    if not circulars:
        logger.warning("No circulars fetched. Exiting.")
        write_log([])
        return

    logger.info(f"\n🔍 STEP 2: Matching {len(KEYWORDS)} keywords...")
    matched = find_matches(circulars)

    logger.info("\n📝 STEP 3: Writing log...")
    log_path = write_log(matched, from_date=from_date, to_date=to_date,
                         keywords_used=KEYWORDS)

    logger.info(f"\n✅ Done. {len(matched)} match(es). Log → {log_path}\n")


# ── Mode 2: Interactive Search ───────────────────────────────

def run_interactive():
    """Interactive mode — user enters keywords + date range."""
    print_banner()
    print("  INTERACTIVE SEARCH MODE")
    print("=" * 60)

    # ── Keyword input ────────────────────────────────────────
    print("\n📌 STEP 1: Enter Keywords")
    print(f"   Default keywords: {', '.join(KEYWORDS)}")
    print("   Press ENTER to use defaults, or type custom keywords")
    print("   (comma-separated, e.g: mock, CAS, DR PR)\n")

    kw_input = input("   Keywords > ").strip()

    if kw_input:
        keywords = [k.strip() for k in kw_input.split(",") if k.strip()]
        print(f"   ✅ Using custom keywords: {keywords}")
    else:
        keywords = KEYWORDS
        print(f"   ✅ Using default keywords: {keywords}")

    # ── Date range input ─────────────────────────────────────
    print("\n📅 STEP 2: Enter Date Range (DD-MM-YYYY)")

    today     = datetime.now().strftime("%d-%m-%Y")
    week_ago  = (datetime.now() - timedelta(days=7)).strftime("%d-%m-%Y")

    print(f"   Press ENTER for defaults  [From: {week_ago}  To: {today}]\n")

    while True:
        from_input = input(f"   From date [{week_ago}] > ").strip()
        from_date  = from_input if from_input else week_ago
        if validate_date(from_date):
            break
        print("   ❌ Invalid format. Use DD-MM-YYYY (e.g. 01-09-2026)")

    while True:
        to_input = input(f"   To date   [{today}] > ").strip()
        to_date  = to_input if to_input else today
        if validate_date(to_date):
            break
        print("   ❌ Invalid format. Use DD-MM-YYYY (e.g. 10-09-2026)")

    # ── Fetch ────────────────────────────────────────────────
    print(f"\n📡 STEP 3: Fetching circulars from NSE...")
    print(f"   Range: {from_date} → {to_date}")

    circulars = fetch_circulars(from_date=from_date, to_date=to_date)

    if not circulars:
        print("\n  ❌ Could not fetch circulars. Check your internet / NSE may be down.\n")
        return

    print(f"   ✅ Fetched {len(circulars)} circulars.")

    # ── Match ────────────────────────────────────────────────
    print(f"\n🔍 STEP 4: Matching keywords...")
    matched = find_matches(circulars, custom_keywords=keywords)

    # ── Show on screen ───────────────────────────────────────
    print_results_to_screen(matched, keywords, from_date, to_date)

    # ── Save to log ──────────────────────────────────────────
    if matched:
        save = input("\n  💾 Save results to log file? (y/n) > ").strip().lower()
        if save == "y":
            log_path = write_log(matched, from_date=from_date, to_date=to_date,
                                 keywords_used=keywords)
            print(f"  ✅ Saved → {log_path}\n")
        else:
            print("  Results not saved.\n")


# ── Entry point ──────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NSE Circular Monitor")
    parser.add_argument(
        "--search",
        action="store_true",
        help="Launch interactive keyword + date search mode"
    )
    args = parser.parse_args()

    if args.search:
        run_interactive()
    else:
        run_automated()