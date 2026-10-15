"""Main file for generating Double Charge results (books, lookup tables, config files, analysis).

Run it from the math-sdk folder:
    python games/double_charge/run.py

Everything you may want to change is in the "SETTINGS" block below.
"""

import os

from gamestate import GameState
from game_config import GameConfig
from game_optimization import OptimizationSetup
from optimization_program.run_script import OptimizationExecution
from utils.game_analytics.run_analysis import create_stat_sheet
from utils.rgs_verification import execute_all_tests
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs

if __name__ == "__main__":

    # ------------------------------------------------------------------ SETTINGS
    cpus = os.cpu_count() or 2
    num_threads = max(1, min(4, cpus))      # simulation threads. More threads = faster but more RAM.
    rust_threads = max(1, min(8, cpus))     # threads for the Rust optimizer
    batching_size = 1000                    # simulations per thread per batch. KEEP SMALL: big batches eat RAM
    compression = True                      # write .zst books (needed for upload)
    profiling = False

    # Simulations per mode. 100,000 is a good first run; use 1,000,000 for the final upload.
    sims_per_mode = 100_000
    # ---------------------------------------------------------------------------

    run_conditions = {
        "run_sims": True,
        "run_optimization": True,    # needs Rust (see README). Set False and use tools/fallback_weights.py if you can't install it
        "run_analysis": True,
        "run_format_checks": True,
    }

    config = GameConfig()
    target_modes = [bm.get_name() for bm in config.bet_modes]     # "base" (+ the bonus buys if enabled)

    # The number of simulations must divide evenly into (threads x batch size).
    chunk = num_threads * batching_size
    sims = max(chunk, (sims_per_mode // chunk) * chunk)
    num_sim_args = {mode: int(sims) for mode in target_modes}

    gamestate = GameState(config)
    if run_conditions["run_optimization"] or run_conditions["run_analysis"]:
        optimization_setup_class = OptimizationSetup(config)

    if run_conditions["run_sims"]:
        create_books(
            gamestate,
            config,
            num_sim_args,
            batching_size,
            num_threads,
            compression,
            profiling,
        )

    generate_configs(gamestate)

    if run_conditions["run_optimization"]:
        OptimizationExecution().run_all_modes(config, target_modes, rust_threads)
        generate_configs(gamestate)

    if run_conditions["run_analysis"]:
        custom_keys = [{"symbol": "scatter"}]
        create_stat_sheet(gamestate, custom_keys=custom_keys)

    if run_conditions["run_format_checks"]:
        execute_all_tests(config)
