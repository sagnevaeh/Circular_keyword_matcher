# ============================================================
# scheduler.py
#
# Keeps running in the background and fires main.run()
# every day at 06:30 AM.
#
# HOW TO START IT:
#   python scheduler.py
#
# HOW TO RUN IN BACKGROUND (Linux/Mac):
#   nohup python scheduler.py &
#
# HOW TO STOP IT:
#   Find the process: ps aux | grep scheduler.py
#   Kill it:          kill <PID>
# ============================================================

import schedule
import time
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("scheduler")


def job():
    logger.info("⏰ Scheduled trigger fired — running main.py...")
    from main import run
    run()


# ── Schedule: every day at 06:30 AM ────────────────────────
schedule.every().day.at("06:30").do(job)

logger.info("🗓  Scheduler started. Will run every day at 06:30 AM.")
logger.info("   Press Ctrl+C to stop.\n")

# ── Keep the script alive forever ──────────────────────────
while True:
    schedule.run_pending()
    time.sleep(30)   # check every 30 seconds