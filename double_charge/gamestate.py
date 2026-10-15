"""Handles the state and output for a single Double Charge simulation round."""

from game_override import GameStateOverride
from src.calculations.lines import Lines
from src.events.events import reveal_event


class GameState(GameStateOverride):
    """Handle all game-logic and event updates for a given simulation number."""

    def run_spin(self, sim, simulation_seed=None):
        """Entry point for every bet mode (base game and the four bonus buys)."""
        self.reset_seed(sim)
        self.repeat = True
        while self.repeat:
            self.reset_book()
            self.draw_board(emit_event=True)

            self.win_data = Lines.get_lines(self.board, self.config, global_multiplier=self.global_multiplier)
            Lines.record_lines_wins(self)
            self.win_manager.update_spinwin(self.win_data["totalWin"])
            Lines.emit_linewin_events(self)

            self.win_manager.update_gametype_wins(self.gametype)
            if self.check_fs_condition() and self.check_freespin_entry():
                self.run_freespin_from_base()

            self.evaluate_finalwin()
            self.check_repeat()

        self.imprint_wins()

    def run_freespin(self):
        """Free spins: sticky Tide Wilds, random bombs, growing Kraken."""
        self.reset_fs_spin()
        self.reset_wild_state()

        while self.fs < self.tot_fs and not self.wincap_triggered:
            self.update_freespin()
            self.draw_board(emit_event=False)
            self.paint_wilds_on_board()          # wilds that are already stuck from earlier spins
            reveal_event(self)

            self.land_new_tide_wilds()
            self.drop_bombs()
            self.grow_or_spawn_kraken()
            self.paint_wilds_on_board()          # final wild layout for this spin
            self.emit_wild_state()

            self.win_data = Lines.get_lines(self.board, self.config, global_multiplier=self.global_multiplier)
            Lines.record_lines_wins(self)
            self.win_manager.update_spinwin(self.win_data["totalWin"])
            Lines.emit_linewin_events(self)
            self.win_manager.update_gametype_wins(self.gametype)

        self.end_freespin()
