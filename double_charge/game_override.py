from game_executables import GameExecutables


class GameStateOverride(GameExecutables):
    """Extends/overrides universal state functions for Double Charge."""

    def reset_book(self):
        """Reset game specific properties."""
        super().reset_book()
        self.reset_wild_state()

    def assign_special_sym_function(self):
        # Wild multipliers are assigned by the feature logic itself, not when a symbol is created.
        self.special_symbol_functions = {}

    def check_repeat(self) -> None:
        """Checks if the spin failed a criteria constraint at any point."""
        if self.repeat is False:
            win_criteria = self.get_current_betmode_distributions().get_win_criteria()
            if win_criteria is not None and self.final_win != win_criteria:
                self.repeat = True

            if self.get_current_distribution_conditions()["force_freegame"] and not (self.triggered_freegame):
                self.repeat = True

            if self.win_manager.running_bet_win == 0.0 and self.criteria != "0":
                self.repeat = True

            # Only the dedicated "wincap" criteria may produce a max-win round.
            if self.wincap_triggered and self.criteria != "wincap":
                self.repeat = True

        self.repeat_count += 1
        self.check_current_repeat_count(warn_after_count=100000)
