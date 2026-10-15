"""Pure-Python stand-in for the Rust optimizer (use it only if you cannot install Rust).

What it does
  The SDK made thousands of simulated rounds ("books"), each tagged with a criteria
  (0, basegame, freegame, wincap). The optimizer's job is to choose HOW OFTEN each book is played so that
    * every criteria appears with the hit rate set in game_optimization.py, and
    * the criteria's average payout gives its share of the 96% RTP.
  This script does that with one smooth weighting rule per criteria (exponential tilting): small wins get
  more weight and big wins less (or the other way round) until the average payout matches exactly.
  It writes library/publish_files/lookUpTable_<mode>_0.csv in the same format as the Rust optimizer
  (weight = probability x 2^50).

Run from the math-sdk folder, after run.py created the books:
    python games/double_charge/tools/fallback_weights.py
"""

import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(GAME, "..", ".."))
sys.path[:0] = [ROOT, GAME]

from game_config import GameConfig  # noqa: E402
from game_optimization import OptimizationSetup  # noqa: E402

LIB = os.path.join(GAME, "library")
SCALE = 2.0 ** 50


def tilt_weights(x: np.ndarray, target_mean: float) -> np.ndarray:
    """Probabilities p_i proportional to exp(-t*x_i/xmax) whose mean of x equals target_mean."""
    xmax = float(x.max())
    if xmax == float(x.min()):                    # all books pay the same (e.g. the 0 and wincap buckets)
        return np.full(len(x), 1.0 / len(x))
    lo_m, hi_m = float(x.min()), xmax
    if not (lo_m <= target_mean <= hi_m):
        raise ValueError(f"target mean {target_mean:.3f} outside simulated range [{lo_m:.3f}, {hi_m:.3f}]")
    xs = x / xmax

    def mean_for(t):
        z = -t * xs
        z -= z.max()
        p = np.exp(z)
        p /= p.sum()
        return float((p * x).sum()), p

    lo, hi = -400.0, 400.0           # mean decreases as t grows
    for _ in range(300):
        mid = (lo + hi) / 2
        m, _p = mean_for(mid)
        if m > target_mean:
            lo = mid
        else:
            hi = mid
    return mean_for((lo + hi) / 2)[1]


def main() -> None:
    config = GameConfig()
    OptimizationSetup(config)
    out_dir = os.path.join(LIB, "publish_files")
    os.makedirs(out_dir, exist_ok=True)
    for bm in config.bet_modes:
        mode, cost = bm.get_name(), bm.get_cost()
        seg = list(csv.reader(open(os.path.join(LIB, "lookup_tables", f"lookUpTableSegmented_{mode}.csv"))))
        ids = np.array([int(r[0]) for r in seg])
        crit = np.array([r[1] for r in seg])
        # payout multiplier (x total bet). Base + free-game wins are summed and then clamped to the win cap,
        # exactly like the SDK does for the real books (a round can never pay more than the max win).
        pay = np.minimum(np.array([float(r[2]) + float(r[3]) for r in seg]), float(bm.get_wincap()))
        conds = config.opt_params[mode]["conditions"]

        # 1) probability of each criteria
        prob, remainder = {}, None
        for name, c in conds.items():
            hr = c.get("hr")
            if isinstance(hr, (int, float)):
                prob[name] = 1.0 / hr
            elif c.get("av_win"):
                prob[name] = c["rtp"] * cost / c["av_win"]
            else:
                remainder = name
        if remainder is None:
            remainder = [n for n in conds if n not in prob][0] if len(prob) < len(conds) else None
        if remainder is not None:
            prob[remainder] = 1.0 - sum(prob.values())
        # 2) mean payout of each criteria  (rtp share * cost / probability)
        weights = np.zeros(len(ids))
        for name, c in conds.items():
            sel = crit == name
            if not sel.any():
                raise RuntimeError(f"No simulations for criteria '{name}' in mode {mode}")
            mean = c["rtp"] * cost / prob[name] if prob[name] > 0 else 0.0
            p_within = tilt_weights(pay[sel], mean)
            weights[sel] = prob[name] * p_within
        wint = np.round(weights * SCALE).astype(np.uint64)
        with open(os.path.join(out_dir, f"lookUpTable_{mode}_0.csv"), "w") as f:
            for i, w, p in zip(ids, wint, pay):
                f.write(f"{int(i)},{int(w)},{int(round(p * 100))}\n")
        print(f"{mode:9s} weights written  (RTP {float((weights*pay).sum())/cost:.4f})")


if __name__ == "__main__":
    main()
