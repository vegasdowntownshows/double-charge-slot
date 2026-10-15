"""Free-spin feature logic for Double Charge.

State kept for the whole free-spin round
  tide_wilds   {(reel,row): multiplier}   sticky single-cell wilds; multiplier 0 means "no multiplier yet"
  kraken_cells [(reel,row), ...]          the growing Kraken Wild (one shared multiplier)
  kraken_mult  int                        1 = no multiplier yet

Per free spin, in this order
  1. new Tide Wilds land on random free cells (sticky)
  2. bombs drop on random cells, any reel/row, each with a 2x-1000x multiplier
        - on a Tide Wild  -> multiplier is added to that wild
        - on the Kraken   -> multiplier is added to the Kraken (shared by all its cells)
        - on any other cell -> the blast opens a new Tide Wild that already carries the multiplier
  3. an existing Kraken grows; if there is none and 3+ Tide Wilds are out, a Kraken is born
  4. all wilds are painted onto the board and lines are evaluated
     (a line win is multiplied by the SUM of the multipliers of the wilds on that line)
"""

import random
from game_calculations import GameCalculations
from game_events import (
    new_tide_wilds_event,
    bomb_drop_event,
    kraken_spawn_event,
    kraken_grow_event,
    wild_state_event,
)
from src.calculations.statistics import get_random_outcome
from src.events.events import fs_trigger_event


class GameExecutables(GameCalculations):
    """Executable functions used by Double Charge."""

    # ------------------------------------------------------------------ state
    def reset_wild_state(self) -> None:
        self.tide_wilds = {}
        self.kraken_cells = []
        self.kraken_mult = 1

    def _all_cells(self) -> list:
        return [(r, c) for r in range(self.config.num_reels) for c in range(self.config.num_rows[r])]

    def _free_cells(self) -> list:
        """Cells holding neither a Tide Wild nor a Kraken cell."""
        return [p for p in self._all_cells() if p not in self.tide_wilds and p not in self.kraken_cells]

    # ------------------------------------------------------------------ free spin count
    def update_freespin_amount(self, scatter_key: str = "scatter") -> None:
        """Spins awarded: 10 from the base game, or the bought amount in the bonus-buy modes."""
        self.tot_fs = self.config.mode_free_spins.get(self.betmode, 10)
        fs_trigger_event(self, basegame_trigger=True, freegame_trigger=False)

    # ------------------------------------------------------------------ feature steps
    def paint_wilds_on_board(self) -> None:
        """Overwrite board cells with the current sticky wilds."""
        for (r, c), mult in self.tide_wilds.items():
            sym = self.create_symbol("W")
            sym.assign_attribute({"multiplier": max(mult, 1)})
            self.board[r][c] = sym
        for r, c in self.kraken_cells:
            sym = self.create_symbol("K")
            sym.assign_attribute({"multiplier": max(self.kraken_mult, 1)})
            self.board[r][c] = sym

    def land_new_tide_wilds(self) -> None:
        n = get_random_outcome(self.get_current_distribution_conditions()["landing_wilds"])
        free = self._free_cells()
        chosen = random.sample(free, min(n, len(free)))
        for pos in chosen:
            self.tide_wilds[pos] = 0
        if chosen:
            new_tide_wilds_event(self, chosen)

    def drop_bombs(self) -> None:
        cond = self.get_current_distribution_conditions()
        n = get_random_outcome(cond["bomb_counts"])
        for _ in range(n):
            reel = random.randrange(self.config.num_reels)
            row = random.randrange(self.config.num_rows[reel])
            mult = get_random_outcome(cond["bomb_mults"])
            pos = (reel, row)
            if pos in self.kraken_cells:
                self.kraken_mult = mult if self.kraken_mult <= 1 else self.kraken_mult + mult
                bomb_drop_event(self, reel, row, mult, "kraken", self.kraken_mult)
            elif pos in self.tide_wilds:
                cur = self.tide_wilds[pos]
                self.tide_wilds[pos] = mult if cur <= 1 else cur + mult
                bomb_drop_event(self, reel, row, mult, "merge", self.tide_wilds[pos])
            else:
                self.tide_wilds[pos] = mult
                bomb_drop_event(self, reel, row, mult, "spawn", mult)

    def grow_or_spawn_kraken(self) -> None:
        cond = self.get_current_distribution_conditions()
        if self.kraken_cells:
            grow = get_random_outcome(cond["kraken_growth"])
            new_cells = []
            for _ in range(grow):
                if len(self.kraken_cells) >= self.config.kraken_max_cells:
                    break
                candidates = []
                for (r, c) in self.kraken_cells:
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.config.num_reels and 0 <= nc < self.config.num_rows[nr]:
                            p = (nr, nc)
                            if p not in self.kraken_cells and p not in self.tide_wilds and p not in candidates:
                                candidates.append(p)
                if not candidates:
                    break
                cell = random.choice(candidates)
                self.kraken_cells.append(cell)
                new_cells.append(cell)
            if new_cells:
                kraken_grow_event(self, new_cells)
        elif len(self.tide_wilds) >= self.config.kraken_trigger_wilds:
            free = self._free_cells()
            if free:
                cell = random.choice(free)
                self.kraken_cells = [cell]
                self.kraken_mult = 1
                kraken_spawn_event(self, cell)

    def emit_wild_state(self) -> None:
        wild_state_event(self)
