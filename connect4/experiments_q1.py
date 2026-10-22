# ------------------------------------------------------------------------
# experiments_q1.py
# Question 1 - Experiments for the report.
#
# Every experiment changes ONE setting of the move generator and keeps the
# others at the base values. Each configuration is run `--runs` times
# (seeds 0, 1, 2, ...) on every test position in tests/positions_q1.json.
#
#   A  number of cycles (iterations)
#   B  utility function (objective weight w, bias type, exploration c)
#   C  expansion nodes (x = children added per expansion)
#   D  height of the tree (max_depth)
#   E  repeatability (same seed vs different seeds)
#   F  tournaments: full games between two configurations
#
# Results are written to results/experiments_q1.csv (every single search)
# and results/experiments_q1.md (summary tables used in answers.md).
#
# Run from the project root (takes about 10-15 minutes):
#   python -m connect4.experiments_q1
#   python -m connect4.experiments_q1 --runs 3 --games 4      (quick version)
# ------------------------------------------------------------------------

import argparse
import csv
import json
import time
from collections import Counter
from dataclasses import replace
from pathlib import Path

from connect4.game_q1 import X, O, ConnectFour
from connect4.mcts_q1 import MCTSConfig, MCTSPlayer, RandomPlayer, monte_carlo_tree_search, tree_size
from connect4.play_q1 import play_game

ROOT = Path(__file__).resolve().parent.parent
POSITIONS = json.loads((ROOT / "tests" / "positions_q1.json").read_text())

# Base settings. 200 iterations is low enough that the effect of each
# setting is still visible (with thousands of iterations every setting
# eventually finds the same moves).
BASE = MCTSConfig(iterations=200, expand_width=7, max_depth=None, c=1.4, w=1.0, bias="decay")

EXPERIMENTS = {
    "A. Number of cycles (iterations)": [
        (f"iterations={n}", replace(BASE, iterations=n)) for n in (25, 50, 100, 200, 500, 1000, 2000)
    ],
    "B. Utility function": [
        ("UCB1 only (w=0)",              replace(BASE, w=0.0)),
        ("w=0.5, decaying",              replace(BASE, w=0.5)),
        ("w=1, decaying (base)",         BASE),
        ("w=2, decaying",                replace(BASE, w=2.0)),
        ("w=5, decaying",                replace(BASE, w=5.0)),
        ("w=1, constant",                replace(BASE, bias="constant")),
        ("c=0.5 (less exploration)",     replace(BASE, c=0.5)),
        ("c=2.5 (more exploration)",     replace(BASE, c=2.5)),
    ],
    "C. Expansion nodes (x)": [
        (f"x={x}", replace(BASE, expand_width=x)) for x in (1, 2, 3, 5, 7)
    ],
    "D. Height of the tree": [
        (f"max_depth={d}", replace(BASE, max_depth=d)) for d in (1, 2, 3, 5, None)
    ],
}

# Each tournament: (label, config for player 1, config for player 2 or "random").
TOURNAMENTS = [
    ("base vs Random",                BASE,                            "random"),
    ("w=1 vs UCB1 only (w=0)",        BASE,                            replace(BASE, w=0.0)),
    ("x=3 vs x=7",                    replace(BASE, expand_width=3),   BASE),
    ("max_depth=2 vs no limit",       replace(BASE, max_depth=2),      BASE),
    ("1000 vs 200 iterations",        replace(BASE, iterations=1000),  BASE),
]


def run_config(game, config, runs):
    # Runs one configuration `runs` times on every position.
    rows = []
    for position in POSITIONS:
        state = game.play(position["moves"])
        for seed in range(runs):
            start = time.perf_counter()
            move, root = monte_carlo_tree_search(game, state, replace(config, seed=seed))
            elapsed = (time.perf_counter() - start) * 1000
            nodes, deepest = tree_size(root)
            best = position["best"]
            rows.append({
                "position": position["name"], "type": position["type"], "seed": seed, "move": move,
                "correct": "" if best is None else int(move in best),
                "time_ms": round(elapsed, 1), "nodes": nodes, "deepest": deepest,
            })
    return rows


def distribution(moves):
    # [3, 3, 4] -> "3:2 4:1" (move:how many times), most common first
    return " ".join(f"{m}:{n}" for m, n in Counter(moves).most_common())


def summarise(rows):
    # One summary row per configuration.
    tactical = [r for r in rows if r["type"] == "tactical"]
    quiet = {}
    for r in rows:
        if r["type"] == "quiet":
            quiet.setdefault(r["position"], []).append(r["move"])
    # "agreement" = share of runs that picked the most common move
    agreement = [Counter(m).most_common(1)[0][1] / len(m) for m in quiet.values()]
    return {
        "tactical_pct": 100 * sum(r["correct"] for r in tactical) / len(tactical),
        "agreement_pct": 100 * sum(agreement) / len(agreement),
        "empty": distribution(quiet["empty_board"]),
        "opening_2": distribution(quiet["opening_2"]),
        "midgame": distribution(quiet["midgame"]),
        "time_ms": sum(r["time_ms"] for r in rows) / len(rows),
        "nodes": sum(r["nodes"] for r in rows) / len(rows),
        "deepest": sum(r["deepest"] for r in rows) / len(rows),
    }


def tournament(game, config_a, config_b, games):
    # Plays `games` games, swapping who goes first every game so neither
    # side gets the first-move advantage more often. Returns (wins A, wins B, draws).
    wins_a = wins_b = draws = 0
    for g in range(games):
        player_a = MCTSPlayer(replace(config_a, seed=1000 + g))
        player_b = RandomPlayer(2000 + g) if config_b == "random" else MCTSPlayer(replace(config_b, seed=2000 + g))
        a_symbol = X if g % 2 == 0 else O
        winner = play_game(game, player_a, player_b) if a_symbol == X else play_game(game, player_b, player_a)
        if winner is None:
            draws += 1
        elif winner == a_symbol:
            wins_a += 1
        else:
            wins_b += 1
    return wins_a, wins_b, draws


def repeatability(game, runs):
    # Experiment E: does the generator always produce the same move?
    #   same seed      -> the random playouts are identical every time
    #   different seed -> the random playouts differ
    rows = []
    for name in ("empty_board", "opening_2", "midgame", "block_diagonal"):
        position = next(p for p in POSITIONS if p["name"] == name)
        state = game.play(position["moves"])
        same = [monte_carlo_tree_search(game, state, replace(BASE, seed=7))[0] for _ in range(runs)]
        different = [monte_carlo_tree_search(game, state, replace(BASE, seed=s))[0] for s in range(runs)]
        rows.append((name, distribution(same), distribution(different)))
    return rows


def main():
    parser = argparse.ArgumentParser(description="Run the MCTS experiments for the report")
    parser.add_argument("--runs", type=int, default=10, help="runs (seeds) per configuration and position")
    parser.add_argument("--games", type=int, default=20, help="games per tournament")
    parser.add_argument("--out", default=str(ROOT / "results"), help="output folder")
    args = parser.parse_args()

    game = ConnectFour()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    tactical = [p["name"] for p in POSITIONS if p["type"] == "tactical"]

    md = ["# Question 1 - Experiment results", "",
          f"Base settings: `{BASE}`  ",
          f"Each configuration: {args.runs} runs (seeds 0-{args.runs - 1}) x {len(POSITIONS)} positions.  ",
          f"Tactical positions ({len(tactical)}): {', '.join(tactical)}.  ",
          "Move distributions are written `move:count`, most common first.", ""]
    all_rows = []

    for title, configs in EXPERIMENTS.items():
        print(f"\n== {title}")
        md += [f"## {title}", "",
               "| Setting | Tactical correct | Same-move agreement (quiet) | Empty board | Opening (3,3) | Midgame | ms / search | Tree nodes | Deepest level |",
               "|---|---|---|---|---|---|---|---|---|"]
        for label, config in configs:
            rows = run_config(game, config, args.runs)
            for r in rows:
                all_rows.append({"experiment": title, "setting": label, **r})
            s = summarise(rows)
            print(f"  {label:28} tactical {s['tactical_pct']:5.1f}%  agreement {s['agreement_pct']:5.1f}%  "
                  f"empty [{s['empty']}]  {s['time_ms']:.0f} ms")
            md.append(f"| {label} | {s['tactical_pct']:.1f}% | {s['agreement_pct']:.1f}% | {s['empty']} | "
                      f"{s['opening_2']} | {s['midgame']} | {s['time_ms']:.0f} | {s['nodes']:.0f} | {s['deepest']:.1f} |")
        md.append("")

    print("\n== E. Repeatability")
    md += ["## E. Repeatability (base settings)", "",
           f"| Position | Same seed (7) run {args.runs} times | Seeds 0-{args.runs - 1} |", "|---|---|---|"]
    for name, same, different in repeatability(game, args.runs):
        print(f"  {name:15} same seed [{same}]   different seeds [{different}]")
        md.append(f"| {name} | {same} | {different} |")
    md.append("")

    print("\n== F. Tournaments")
    md += ["## F. Tournaments (first player alternates every game)", "",
           "| Match (A vs B) | A wins | B wins | Draws |", "|---|---|---|---|"]
    for label, config_a, config_b in TOURNAMENTS:
        a, b, d = tournament(game, config_a, config_b, args.games)
        print(f"  {label:28} {a}-{b} (draws {d})")
        md.append(f"| {label} | {a} | {b} | {d} |")
    md.append("")

    with open(out / "experiments_q1.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_rows)
    (out / "experiments_q1.md").write_text("\n".join(md), encoding="utf-8")
    print(f"\nSaved {out / 'experiments_q1.csv'} and {out / 'experiments_q1.md'}")


if __name__ == "__main__":
    main()
