"""Reads the finished lookup tables and prints RTP, hit rate and max-win odds for every mode.

Run from the math-sdk folder AFTER run.py has finished:
    python games/double_charge/tools/verify_rtp.py

It reads library/publish_files/ (these are the tables Stake uses). If the Rust optimizer has not run yet the
weights are all equal and the RTP you see is the "raw" RTP - it will not match 96% until the optimizer has run.
"""

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PUBLISH = os.path.join(HERE, "..", "library", "publish_files")
TARGET_RTP = 0.96
MAX_WIN = 50000


def main() -> int:
    index_path = os.path.join(PUBLISH, "index.json")
    if not os.path.exists(index_path):
        print("index.json not found - run games/double_charge/run.py first.")
        return 1
    modes = json.load(open(index_path))["modes"]
    ok = True
    print(f"{'mode':10s} {'cost':>6s} {'RTP':>8s} {'hit rate':>10s} {'max win':>9s} {'max-win odds':>14s}  result")
    for m in modes:
        total_w = pay_w = hit_w = cap_w = 0.0
        top = 0.0
        with open(os.path.join(PUBLISH, m["weights"]), newline="") as f:
            for row in csv.reader(f):
                weight, payout = float(row[1]), float(row[2]) / 100.0
                total_w += weight
                pay_w += weight * payout
                if payout > 0:
                    hit_w += weight
                if payout >= MAX_WIN:
                    cap_w += weight
                top = max(top, payout)
        rtp = pay_w / total_w / m["cost"]
        hit = hit_w / total_w
        odds = f"1 in {total_w / cap_w:,.0f}" if cap_w else "never"
        good = abs(rtp - TARGET_RTP) <= 0.002 and top <= MAX_WIN and cap_w > 0
        ok &= good
        print(f"{m['name']:10s} {m['cost']:6.1f} {rtp:8.4f} {hit:10.4f} {top:9.0f} {odds:>14s}  {'OK' if good else 'CHECK'}")
    print("\nAll modes within 0.2% of the 96% target." if ok else "\nSome modes are off target - see README 'If RTP is off'.")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
