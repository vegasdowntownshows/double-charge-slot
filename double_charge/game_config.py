"""Double Charge - game configuration.

Ocean-themed 5x4 line slot for Stake Engine.
  * 20 paylines, 3/4/5 of a kind pay left to right.
  * 3+ scatters trigger 10 free spins.
  * During free spins: sticky Tide Wilds, random Bomb drops (2x-1000x) and a growing Kraken Wild.
  * Max win 50,000x.

Everything a game designer would want to tweak (RTP target, bomb odds, wild odds, costs, ...) lives in this file.
"""

import os
from src.config.config import Config
from src.config.distributions import Distribution
from src.config.betmode import BetMode


class GameConfig(Config):
    """Double Charge configuration."""

    def __init__(self):
        super().__init__()
        self.game_id = "double_charge"
        self.provider_number = 0
        self.working_name = "Double Charge"
        self.wincap = 50000
        self.win_type = "lines"
        self.rtp = 0.96
        self.construct_paths()

        # ------------------------------------------------------------------ board
        self.num_reels = 5
        self.num_rows = [4] * self.num_reels

        # ------------------------------------------------------------------ paytable (x total bet)
        # H = high pay "treasure" symbols, L = low pay "sea life" symbols, W = Tide Wild (also pays on its own)
        self.paytable = {
            (5, "W"): 20, (4, "W"): 8, (3, "W"): 3,
            (5, "H1"): 40, (4, "H1"): 16, (3, "H1"): 6,
            (5, "H2"): 24, (4, "H2"): 10, (3, "H2"): 4,
            (5, "H3"): 16, (4, "H3"): 6, (3, "H3"): 2.4,
            (5, "H4"): 12, (4, "H4"): 4, (3, "H4"): 1.6,
            (5, "L1"): 6, (4, "L1"): 2, (3, "L1"): 0.8,
            (5, "L2"): 6, (4, "L2"): 1.6, (3, "L2"): 0.6,
            (5, "L3"): 4, (4, "L3"): 1.2, (3, "L3"): 0.5,
            (5, "L4"): 4, (4, "L4"): 1, (3, "L4"): 0.4,
            (5, "L5"): 3, (4, "L5"): 0.8, (3, "L5"): 0.3,
        }
        # 20 paylines: value = row index used on each of the 5 reels (0 = top row)
        self.paylines = {
            1: [0, 0, 0, 0, 0], 2: [1, 1, 1, 1, 1], 3: [2, 2, 2, 2, 2], 4: [3, 3, 3, 3, 3],
            5: [0, 1, 2, 1, 0], 6: [3, 2, 1, 2, 3], 7: [1, 0, 0, 0, 1], 8: [2, 3, 3, 3, 2],
            9: [0, 0, 1, 2, 3], 10: [3, 3, 2, 1, 0], 11: [1, 2, 3, 2, 1], 12: [2, 1, 0, 1, 2],
            13: [0, 1, 1, 1, 0], 14: [3, 2, 2, 2, 3], 15: [1, 1, 0, 1, 1], 16: [2, 2, 3, 2, 2],
            17: [0, 1, 0, 1, 0], 18: [3, 2, 3, 2, 3], 19: [1, 2, 1, 2, 1], 20: [2, 1, 2, 1, 2],
        }
        self.include_padding = True

        # W = Tide Wild (sticky in free spins), K = Kraken Wild (growing), S = scatter
        self.special_symbols = {
            "wild": ["W", "K"],
            "scatter": ["S"],
            "multiplier": ["W", "K"],
        }

        # ------------------------------------------------------------------ free spins
        # Number of scatters -> number of free spins. No retriggers.
        self.freespin_triggers = {self.basegame_type: {3: 10, 4: 10, 5: 10}}
        self.anticipation_triggers = {
            self.basegame_type: min(self.freespin_triggers[self.basegame_type].keys()) - 1,
        }
        # Spins awarded by each bought bonus mode. (Stateless: the "gamble up to 25 spins" idea is
        # offered as four separate buy modes instead of a live gamble - see README.)
        self.mode_free_spins = {"bonus_10": 10, "bonus_15": 15, "bonus_20": 20, "bonus_25": 25}

        # ------------------------------------------------------------------ feature settings
        self.kraken_trigger_wilds = 3     # 3+ Tide Wilds on the board -> a Kraken Wild is born
        self.kraken_max_cells = 6         # Kraken stops growing at this many cells

        # True  -> base game + four bonus-buy modes (10 / 15 / 20 / 25 free spins)
        # False -> base game only (the base game is the part that passes the SDK's volatility checks, see README)
        self.enable_bonus_buys = True

        # ------------------------------------------------------------------ reels
        reels = {"BR0": "BR0.csv", "FR0": "FR0.csv"}
        self.reels = {}
        for r, f in reels.items():
            self.reels[r] = self.read_reels_csv(os.path.join(self.reels_path, f))
        self.padding_reels = {"basegame": self.reels["BR0"], "freegame": self.reels["FR0"]}

        # ------------------------------------------------------------------ feature tables
        # Every table is {value: weight}. "Normal" tables are used for ordinary free games,
        # "WINCAP" tables are far more generous and are only used to build the 50,000x outcomes.
        fs_normal = {
            "landing_wilds": {0: 880, 1: 105, 2: 13, 3: 2},            # new Tide Wilds per spin
            "bomb_counts": {0: 930, 1: 62, 2: 7, 3: 1},               # bombs dropped per spin
            "bomb_mults": {                                            # bomb multiplier values
                2: 300, 3: 220, 4: 150, 5: 110, 8: 60, 10: 40, 15: 20,
                20: 12, 25: 8, 50: 3, 100: 1, 250: 0.3, 500: 0.1, 1000: 0.04,
            },
            "kraken_growth": {0: 50, 1: 50},                           # cells the Kraken grows per spin
        }
        fs_wincap = {
            "landing_wilds": {0: 200, 1: 400, 2: 300, 3: 100},
            "bomb_counts": {0: 250, 1: 400, 2: 250, 3: 100},
            "bomb_mults": {
                2: 50, 3: 50, 4: 50, 5: 60, 8: 60, 10: 80, 15: 80,
                20: 90, 25: 90, 50: 100, 100: 110, 250: 100, 500: 80, 1000: 60,
            },
            "kraken_growth": {1: 40, 2: 60},
        }

        def scaled(tables, spins):
            """Longer bonuses get proportionally fewer wild/bomb drops per spin, so the feature stays balanced."""
            factor = 10.0 / spins
            out = dict(tables)
            for key in ("landing_wilds", "bomb_counts"):
                t = tables[key]
                nz = {k: v * factor for k, v in t.items() if k != 0}
                out[key] = {0: sum(t.values()) - sum(nz.values()), **nz}
            return out

        def conds(tables, scatter_triggers, force_freegame, force_wincap=False, base_only=False):
            c = {
                "reel_weights": {self.basegame_type: {"BR0": 1}, self.freegame_type: {"FR0": 1}},
                "force_wincap": force_wincap,
                "force_freegame": force_freegame,
            }
            if base_only:
                c["reel_weights"] = {self.basegame_type: {"BR0": 1}}
            else:
                c.update({"scatter_triggers": scatter_triggers})
                c.update(tables)
            return c

        scatter_normal = {3: 100, 4: 8, 5: 1}
        scatter_wincap = {4: 1, 5: 2}

        def feature_mode(name, cost, is_buybonus, is_feature, extra=None):
            spins = self.mode_free_spins.get(name, 10)
            dists = [
                Distribution(
                    criteria="wincap", quota=0.001, win_criteria=self.wincap,
                    conditions=conds(scaled(fs_wincap, spins), scatter_wincap, True, True),
                ),
                Distribution(
                    criteria="freegame", quota=0.1 if not is_buybonus else 0.999,
                    conditions=conds(scaled(fs_normal, spins), scatter_normal, True),
                ),
            ]
            if extra:
                dists += extra
            return BetMode(
                name=name, cost=cost, rtp=self.rtp, max_win=self.wincap, auto_close_disabled=False,
                is_feature=is_feature, is_buybonus=is_buybonus, distributions=dists,
            )

        base_extra = [
            Distribution(
                criteria="0", quota=0.4, win_criteria=0.0,
                conditions=conds(None, None, False, base_only=True),
            ),
            Distribution(
                criteria="basegame", quota=0.5,
                conditions=conds(None, None, False, base_only=True),
            ),
        ]

        # Costs of the bonus buys are set so each buy mode has the same RTP as the base game.
        # (They are re-derived from simulation results - see README "Tuning".)
        self.bonus_costs = {"bonus_10": 100.0, "bonus_15": 160.0, "bonus_20": 230.0, "bonus_25": 300.0}

        self.bet_modes = [feature_mode("base", 1.0, False, True, base_extra)]
        if self.enable_bonus_buys:
            for mode, cost in self.bonus_costs.items():
                self.bet_modes.append(feature_mode(mode, cost, True, False))
