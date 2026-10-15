"""Plain-Python checks of the Double Charge feature rules. Run from the math-sdk folder:
    python games/double_charge/tools/test_feature_rules.py
Plays 400 free-spin rounds and asserts the rules from the README always hold.
"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path[:0] = [ROOT, os.path.join(ROOT, "games", "double_charge")]

from game_config import GameConfig  # noqa: E402
from gamestate import GameState  # noqa: E402


def check_round(book, cfg, spins_expected):
    prev_tide, prev_kraken = {}, set()
    cur_tide = set()          # Tide Wild cells as the current spin's events unfold
    spins = 0
    for ev in book["events"]:
        t = ev["type"]
        if t == "updateFreeSpin":
            spins += 1
            cur_tide = set(prev_tide)
        if t == "newTideWilds":
            cur_tide |= {(w["reel"], w["row"]) for w in ev["newWilds"]}
        if t == "bombDrop" and ev["effect"] == "spawn":
            cur_tide.add((ev["reel"], ev["row"]))
        if t == "reveal":
            for reel in ev["board"]:
                assert len(reel) == 4 + 2, "board must be 4 rows + 2 padding rows"
        if t == "bombDrop":
            assert 2 <= ev["bombMult"] <= 1000, "bomb multiplier out of range"
            assert 1 <= ev["row"] <= 4 and 0 <= ev["reel"] <= 4, "bomb off the board"
            assert ev["effect"] in ("merge", "kraken", "spawn")
        if t == "wildState":
            tide = {(w["reel"], w["row"]): w["mult"] for w in ev["tideWilds"]}
            kraken = {(c["reel"], c["row"]) for c in ev["kraken"]["cells"]}
            for pos, m in prev_tide.items():                       # sticky: never disappear, never shrink
                assert pos in tide and tide[pos] >= m, "tide wild vanished or lost multiplier"
            assert prev_kraken <= kraken, "kraken lost cells"
            assert len(kraken) <= cfg.kraken_max_cells, "kraken too big"
            assert not (set(tide) & kraken), "tide wild and kraken on same cell"
            prev_tide, prev_kraken = tide, kraken
        if t == "krakenSpawn":
            assert not prev_kraken, "a second Kraken must never spawn"
            assert len(cur_tide) >= cfg.kraken_trigger_wilds, "Kraken needs 3+ Tide Wilds on the board"
    assert spins <= spins_expected
    assert book["payoutMultiplier"] <= cfg.wincap * 100


def main():
    cfg = GameConfig()
    for mode, crit, spins, n in [("base", "freegame", 10, 150), ("bonus_15", "freegame", 15, 100),
                                  ("bonus_25", "freegame", 25, 80), ("bonus_10", "wincap", 10, 20)]:
        gs = GameState(GameConfig())
        gs.betmode, gs.criteria = mode, crit
        for bm in gs.config.bet_modes:
            if bm.get_name() == mode:
                gs.config.wincap = bm.get_wincap()
        from src.wins.win_manager import WinManager
        gs.win_manager = WinManager(cfg.basegame_type, cfg.freegame_type, gs.config.wincap)
        gs.library, gs.recorded_events = {}, {}
        for i in range(n):
            gs.run_spin(i)
            book = gs.library[i + 1]
            check_round(book, cfg, spins)
            if crit == "wincap":
                assert book["payoutMultiplier"] == cfg.wincap * 100, "wincap round must pay exactly 50,000x"
        print(f"{mode:9s} {crit:9s} {n:4d} rounds OK")
    print("All feature rules hold.")


if __name__ == "__main__":
    main()
