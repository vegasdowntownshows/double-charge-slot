# Double Charge - math model (Stake Engine)

Ocean-themed 5x4 slot, 20 paylines, 96% RTP, **50,000x max win**.
This folder is the **math part** of the game: it simulates every possible round, writes the files Stake Engine needs
(books + lookup tables), and checks them. The frontend (graphics, animation, sound) is the next step and is built on the
events this math emits (see "Events for the frontend" at the bottom).

---------------------------------------------------------------------------------------------------

## 1. Install and run

You need: **Python 3.12+**, **Git**, and **Rust** (Rust is only for the optimizer, step 5).

```
git clone https://github.com/StakeEngine/math-sdk.git
cd math-sdk
```

Copy this whole `double_charge` folder into `math-sdk/games/` so you have `math-sdk/games/double_charge/run.py`.

**Mac / Linux**
```
make setup
source env/bin/activate
make run GAME=double_charge
```

**Windows (no `make`)**
```
python -m venv env
env\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
python games\double_charge\run.py
```

Install Rust from https://rustup.rs (needed once; the first optimizer run compiles it, a few minutes).

What `run.py` does, in order: 1) simulates rounds for every mode, 2) runs the Rust optimizer which sets how often each
round is played so RTP and hit rates hit their targets, 3) writes statistics (`library/double_charge_full_statistics.xlsx`),
4) runs the SDK's own format checks.

Time: simulating 100,000 rounds x 5 modes took me about 30 minutes on a 2-core machine, plus the optimizer. More cores = faster.

**Output** (this is what you upload): `games/double_charge/library/publish_files/`

**Settings** are at the top of `run.py`. The important ones:
- `sims_per_mode` - 100,000 for tests, 1,000,000 for the final upload.
- `batching_size` - keep at 1000. Big batches use many GB of RAM and crash the run.
- `num_threads` - capped at 4 by default. Raise it only if you have lots of RAM.

---------------------------------------------------------------------------------------------------

## 2. The game rules (as built)

**Board:** 5 reels x 4 rows, 20 fixed paylines, wins pay left to right for 3, 4 or 5 of a kind.

**Symbols** (names are placeholders for your art): `H1`-`H4` high pay, `L1`-`L5` low pay, `W` Tide Wild, `K` Kraken Wild,
`S` scatter. `W` also pays on its own (3/4/5 of a kind = 3x / 8x / 20x).

| Symbol | 3 | 4 | 5 |
|---|---|---|---|
| H1 | 6 | 16 | 40 |
| H2 | 4 | 10 | 24 |
| H3 | 2.4 | 6 | 16 |
| H4 | 1.6 | 4 | 12 |
| L1 | 0.8 | 2 | 6 |
| L2 | 0.6 | 1.6 | 6 |
| L3 | 0.5 | 1.2 | 4 |
| L4 | 0.4 | 1 | 4 |
| L5 | 0.3 | 0.8 | 3 |

(x total bet)

**Free spins:** 3, 4 or 5 scatters = **10 free spins**. No retrigger.

**During free spins, every spin:**
1. **Tide Wilds** (sticky, one cell each) may land on random cells. They stay for the rest of the free spins.
2. **Bombs** (puffer fish / fat fish in the art) may drop on **any cell of any reel**. Each bomb has a multiplier from
   **2x to 1000x**.
   - Bomb lands on a Tide Wild -> its multiplier is added to that wild.
   - Bomb lands on the Kraken -> its multiplier is added to the Kraken (shared by all its cells).
   - Bomb lands on any other cell -> it blows open a new Tide Wild that already carries the multiplier.
3. **Kraken Wild** (the "growing" wild): once **3 or more Tide Wilds** are on the board a Kraken is born on a free cell. After
   that it grows by 0 or 1 cell per spin (50/50) up to **6 cells**.
4. Lines are evaluated. **A line win is multiplied by the SUM of the multipliers of the wilds on that line** (the SDK adds
   them, it does not multiply them).

Plain wilds have no multiplier of their own: only bombs create multipliers.

**Win cap:** any round is cut off at 50,000x. When a round reaches the cap the free spins stop immediately.

**"Gamble for more spins" became four buy modes.** Stake Engine games must be *stateless* (every bet stands alone), so a
live "gamble +5 spins" choice is not allowed. Instead the player picks the bonus size up front, each as its own mode
(each has its own cost and the same 96% RTP):

| Mode | Free spins | Cost |
|---|---|---|
| base | 10 (from 3+ scatters) | 1x |
| bonus_10 | 10 | 100x |
| bonus_15 | 15 | 160x |
| bonus_20 | 20 | 230x |
| bonus_25 | 25 | 300x |

Longer bonuses get proportionally fewer wild/bomb drops per spin so the feature stays balanced.

---------------------------------------------------------------------------------------------------

## 3. Files in this folder

| File | What it is |
|---|---|
| `game_config.py` | **All the numbers**: paytable, paylines, bomb odds/multipliers, wild odds, mode costs, 50,000x cap. Start here when tuning. |
| `game_executables.py` | The free-spin feature logic (tide wilds, bombs, Kraken). |
| `gamestate.py` | One round from start to finish (base game -> free spins). |
| `game_events.py` | The custom events the frontend animates (bomb drop, wild landing, Kraken growth). |
| `game_override.py` | Small overrides of SDK defaults (round repeat rules). |
| `game_optimization.py` | Targets for the optimizer: hit rate and RTP share of each kind of round. |
| `game_calculations.py` | Empty helper file the SDK layout expects. |
| `reels/BR0.csv`, `reels/FR0.csv` | Reel strips for base game and free spins. |
| `run.py` | The one file you run. |
| `tools/verify_rtp.py` | Reads the finished tables and prints RTP, hit rate, max win per mode. |
| `tools/test_feature_rules.py` | Plays hundreds of free-spin rounds and checks every rule above always holds. |
| `tools/fallback_weights.py` | Python stand-in for the Rust optimizer (only if you cannot install Rust). |

---------------------------------------------------------------------------------------------------

## 4. Tuning

All in `game_config.py`:
- **RTP / feel of the bonus:** `fs_normal` tables - `bomb_counts` (how many bombs per spin), `bomb_mults` (which
  multipliers, as weights), `landing_wilds`, `kraken_growth`. More bombs or heavier big multipliers = a wilder bonus.
- **Kraken:** `kraken_trigger_wilds` (3) and `kraken_max_cells` (6).
- **Bonus-buy prices:** `bonus_costs`. The optimizer sets each mode to 96% whatever the cost, so cost mainly decides how
  big the average bonus must be.
- **Bonus buys on/off:** `enable_bonus_buys` (see section 6).
- **Base game hit rates and RTP split:** `game_optimization.py`. The shares must add up to 0.96 in every mode.

After any change: run `python games/double_charge/tools/test_feature_rules.py`, then `run.py`, then
`python games/double_charge/tools/verify_rtp.py`.

### If RTP is off
- Run `run.py` fully (the optimizer step is what brings RTP to 96%). Before it, RTP in the lookup tables is just raw.
- If the optimizer complains that a target is unreachable, the simulations don't contain wins in the range it needs.
  Raise `sims_per_mode`, or make the feature tables in `game_config.py` generate more of the missing win sizes.
- No Rust? Run `python games/double_charge/tools/fallback_weights.py` after `run.py` (with `run_optimization` set to
  `False`). It makes the same kind of table, but it is cruder.

---------------------------------------------------------------------------------------------------

## 5. What was tested, and what was not

Tested (on a small machine, with 10,000 to 40,000 simulations per mode):
- Rules test passes: wilds never disappear or lose multiplier, bombs stay on the board with 2x-1000x, the Kraken never
  exceeds 6 cells and is only born with 3+ Tide Wilds, a capped round pays exactly 50,000x.
- No round in any mode pays more than 50,000x, and the max win exists in every mode.
- RTP = 96.00% in all five modes (using the Python fallback weights).
- The SDK's own checks pass: books and lookup tables match (SHA-256 and payout hashes).
- Base game hit rate about 28%. The bonus frequency (1 in 200 spins) and average bonus (91x) are the *targets* set in
  `game_optimization.py`; the optimizer enforces them, I did not measure them independently.

Note: the sample tables in `library/` hold only 10,000 rounds per mode. They are for checking, not for upload.

**NOT tested - please do these yourself:**
- **The Rust optimizer.** It could not be built in my environment, so all RTP numbers above come from the Python fallback.
  Run the full `run.py` and read the output.
- **Large runs.** Use 1,000,000 sims per mode for the final upload. With small runs the big-win tail is gappy.
- **Stake's upload checks.** Nothing here has been submitted to Stake.

---------------------------------------------------------------------------------------------------

## 6. Known risks before you submit

1. **Volatility warnings on the bonus-buy modes.** The SDK's checker prints "fails 3-star volatility limits"
   (`etl40b`, `etl10k`) for `bonus_10/15/20/25`. The **base game passes with no warning.** I could not find out whether
   Stake treats this as a hard rejection or just a rating, so check Stake's current approval page before submitting.
   Safest first submission: set `enable_bonus_buys = False` in `game_config.py` and submit base-game-only. The base game
   still contains the full feature (free spins, Tide Wilds, bombs up to 1000x, Kraken, 50,000x cap). You can add the buys
   in a later version only if Stake allows changes (after approval only small visual fixes are allowed).
2. **Max-win frequency.** The Rust optimizer is set to pay the base-game max win about 1 in 10,000,000 rounds
   (`WINCAP_RTP = 0.005`). The sample tables that came with this folder were made with the Python fallback instead and show
   the base-game max win at about **1 in 100,000,001** (checked directly from `lookUpTable_base_0.csv`), so the two differ.
   Re-run `run.py` with the optimizer and read the real number from its output. I couldn't confirm Stake's exact
   requirement for how often the max win must occur; check Stake's approval page. To change it, edit `WINCAP_RTP` in
   `game_optimization.py` (and move the same amount into the `basegame` share so the total stays 0.96).
3. **Originality.** "Zeus vs Hades"-style and "Gates"-style mechanics are close to existing games. The mechanics here
   are different (bombs on any cell, a shared-multiplier growing wild), but the theme, symbols and presentation must be
   your own so a reviewer doesn't see a copy.
4. **Approval is at the reviewer's discretion**, and a submitted game must be final.

---------------------------------------------------------------------------------------------------

## Events for the frontend

Every round is a list of events the frontend plays in order. Standard SDK events (`reveal`, `winInfo`, `setWin`,
`setTotalWin`, `freeSpinTrigger`, `updateFreeSpin`, `freeSpinEnd`, `wincap`, `finalWin`) plus these custom ones:

| Event | Meaning | Key fields |
|---|---|---|
| `newTideWilds` | Tide Wilds landed this spin | `newWilds` [{reel,row}] |
| `bombDrop` | One bomb fell | `reel`,`row`,`bombMult`,`effect` (`merge`/`kraken`/`spawn`),`newMult` |
| `krakenSpawn` | The Kraken was born | `cells`,`mult` |
| `krakenGrow` | The Kraken grew | `newCells`,`cells`,`mult` |
| `wildState` | Full snapshot of all sticky wilds after the spin (also used by Bet Replay) | `tideWilds`,`kraken` |

Rows are shifted by +1 (row 0 is the padding symbol above the board), like every SDK event.
