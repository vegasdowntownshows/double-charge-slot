"""Custom events for Double Charge. The frontend plays these in order to animate the feature.

All row values are shifted by +1 when the board has padding (the top padding symbol is row 0),
exactly like the standard SDK events.
"""

from src.events.event_constants import EventConstants  # noqa: F401  (kept for convenience)

NEW_TIDE_WILDS = "newTideWilds"
BOMB_DROP = "bombDrop"
KRAKEN_SPAWN = "krakenSpawn"
KRAKEN_GROW = "krakenGrow"
WILD_STATE = "wildState"


def _pad(gamestate) -> int:
    return 1 if gamestate.config.include_padding else 0


def _cell(gamestate, reel, row) -> dict:
    return {"reel": int(reel), "row": int(row) + _pad(gamestate)}


def new_tide_wilds_event(gamestate, cells: list) -> None:
    """Tide Wilds that landed on this spin (they stay for the rest of the free spins)."""
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": NEW_TIDE_WILDS,
            "newWilds": [_cell(gamestate, r, c) for r, c in cells],
        }
    )


def bomb_drop_event(gamestate, reel, row, bomb_mult, effect, new_mult) -> None:
    """One bomb. effect: 'merge' (joined an existing Tide Wild), 'kraken' (joined the Kraken) or 'spawn' (blew open a new Tide Wild)."""
    ev = {"index": len(gamestate.book.events), "type": BOMB_DROP}
    ev.update(_cell(gamestate, reel, row))
    ev.update({"bombMult": int(bomb_mult), "effect": effect, "newMult": int(new_mult)})
    gamestate.book.add_event(ev)


def kraken_spawn_event(gamestate, cell) -> None:
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": KRAKEN_SPAWN,
            "cells": [_cell(gamestate, *cell)],
            "mult": int(gamestate.kraken_mult),
        }
    )


def kraken_grow_event(gamestate, new_cells: list) -> None:
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": KRAKEN_GROW,
            "newCells": [_cell(gamestate, r, c) for r, c in new_cells],
            "cells": [_cell(gamestate, r, c) for r, c in gamestate.kraken_cells],
            "mult": int(gamestate.kraken_mult),
        }
    )


def wild_state_event(gamestate) -> None:
    """Full snapshot of every sticky wild after the spin's feature actions (also used by Bet Replay)."""
    gamestate.book.add_event(
        {
            "index": len(gamestate.book.events),
            "type": WILD_STATE,
            "tideWilds": [
                {**_cell(gamestate, r, c), "mult": int(max(m, 1))}
                for (r, c), m in sorted(gamestate.tide_wilds.items())
            ],
            "kraken": {
                "cells": [_cell(gamestate, r, c) for r, c in gamestate.kraken_cells],
                "mult": int(gamestate.kraken_mult),
            },
        }
    )
