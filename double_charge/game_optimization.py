"""Optimization settings for Double Charge (used by the SDK's Rust optimizer).

How to read this file
  rtp   = share of the 96% total RTP that this kind of outcome should deliver
  hr    = hit rate, "1 in hr" rounds
  The "freegame" criteria in the base mode has rtp 0.455 and hr 200, so the average bonus pays 0.455 x 200 = 91x.
  Shares in every mode add up to 0.96.
"""

from optimization_program.optimization_config import (
    ConstructScaling,
    ConstructParameters,
    ConstructConditions,
    verify_optimization_input,
)

WINCAP_RTP = 0.005  # max win is paid ~1 in 10 million rounds (0.005 x ... see README)


def _params(test_spins, test_weights):
    return ConstructParameters(
        num_show=5000,
        num_per_fence=10000,
        min_m2m=4,
        max_m2m=8,
        pmb_rtp=1.0,
        sim_trials=5000,
        test_spins=test_spins,
        test_weights=test_weights,
        score_type="rtp",
    ).return_dict()


class OptimizationSetup:
    """Handle all game mode optimization parameters."""

    def __init__(self, game_config):
        self.game_config = game_config
        wincaps = {bm.get_name(): bm.get_wincap() for bm in game_config.bet_modes}

        def bonus_mode(name):
            return {
                "conditions": {
                    "wincap": ConstructConditions(
                        rtp=WINCAP_RTP, av_win=wincaps[name], search_conditions=wincaps[name]
                    ).return_dict(),
                    "freegame": ConstructConditions(rtp=round(0.96 - WINCAP_RTP, 5), hr="x").return_dict(),
                },
                "scaling": ConstructScaling([]).return_dict(),
                "parameters": _params([10, 20, 50], [0.6, 0.2, 0.2]),
            }

        self.game_config.opt_params = {
            "base": {
                "conditions": {
                    "wincap": ConstructConditions(
                        rtp=WINCAP_RTP, av_win=wincaps["base"], search_conditions=wincaps["base"]
                    ).return_dict(),
                    "0": ConstructConditions(rtp=0, av_win=0, search_conditions=0).return_dict(),
                    "freegame": ConstructConditions(
                        rtp=0.455, hr=200, search_conditions={"symbol": "scatter"}
                    ).return_dict(),
                    "basegame": ConstructConditions(hr=3.6, rtp=0.5).return_dict(),
                },
                "scaling": ConstructScaling([]).return_dict(),
                "parameters": _params([50, 100, 200], [0.3, 0.4, 0.3]),
            },
        }
        # The four bonus-buy modes only exist when enable_bonus_buys is True in game_config.py
        for name in wincaps:
            if name != "base":
                self.game_config.opt_params[name] = bonus_mode(name)

        verify_optimization_input(self.game_config, self.game_config.opt_params)
