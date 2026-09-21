# ============================================================
# config/keywords.py
#
# Official keyword list for NSE Circular Monitor.
# Category: Live Trading
#
# Whole-word matching is used — so:
#   "DR PR"    → matches only exact phrase "DR PR"
#   "mock"     → matches "mock" but NOT "mockery"
#   "CAS"      → matches "CAS" but NOT "CAST" or "cascade"
# ============================================================

KEYWORDS = [                           # Disaster Recovery - Primary site switchover
    "DR PR",
    "rebalancing",                      # Index / portfolio rebalancing
    "Mandatory software version changes", # Software upgrade notices
    "partition",                        # Market partition events
    "mock",                             # Mock trading sessions
    "CAS",                              # Closing Auction Session
    "Live Trading",                      # Live trading from DR/PR site
    "PR",
    "cas",
    "Mock",
]