# DPS970 – Activity 2

**Trung Hieu Duong** · Student ID 160982237

The written answers and the Question 1 report are in [answers.md](answers.md).

## Requirements

- Python 3.10 or newer
- pytest (`pip install -r requirements.txt`)

## Project layout

```
connect4/                    # Question 1
  game_q1.py                 #   Connect Four rules (AIMA game interface) + objective evaluation function
  mcts_q1.py                 #   MONTE-CARLO-TREE-SEARCH (AIMA Fig 5.11)
  play_q1.py                 #   plays full games: MCTS vs Random / MCTS / human
  experiments_q1.py          #   runs all the experiments used in the report
logic/                       # Questions 2, 3 and 4
  logic_q234.py              #   truth tables, model counting, CNF conversion, PL-RESOLUTION
results/                     # Question 1 experiment data
  experiments_q1.csv         #   every single search (one row per run)
  experiments_q1.md          #   summary tables (copied into answers.md)
tests/
  positions_q1.json          # Q1 test data: 11 board positions, with the correct move(s) for the 8 tactical ones
  logic_cases_q234.json      # Q2-4 test data: sentences with their expected answers
  test_connect4_q1.py        # Q1 tests: game rules and the objective function
  test_mcts_q1.py            # Q1 tests: selection utility, tree, repeatability, move quality
  test_logic_q234.py         # Q2-4 tests: parser, truth tables, model counts, CNF, resolution
.github/workflows/tests.yml  # runs all tests automatically on GitHub
```

## Running the tests

From the project root folder (the folder containing this README):

```
pip install -r requirements.txt
pytest -v
```

This should show **113 passed** in about 10 seconds.

The same tests run automatically on GitHub Actions (`.github/workflows/tests.yml`) on every push and pull request.

## Running Question 1: Connect Four MCTS

**Pick a move for a position.** Positions are given as the list of columns (0-6) played so far, X first:

```
python -m connect4.mcts_q1                                      # empty board
python -m connect4.mcts_q1 --moves 2 1 3 2 3 4 4 3 6 4 --seed 1  # X must block column 4
```

It prints the board, then the playouts, win rate and objective value of every move, and the chosen move. Options:

| Option | Meaning | Default |
|---|---|---|
| `--iterations N` | number of MCTS cycles | 1000 |
| `--width X` | expansion nodes: children added per expansion (1-7) | 7 |
| `--depth D` | maximum height of the tree | no limit |
| `--c C` | weight of the UCB1 exploration term | 1.4 |
| `--w W` | weight of the objective (rules) term | 1.0 |
| `--bias decay\|constant` | objective term shrinks with playouts, or stays the same | decay |
| `--seed S` | random seed (same seed = same result) | random |

**Play a full game:**

```
python -m connect4.play_q1                             # MCTS (X) vs Random (O)
python -m connect4.play_q1 --o mcts --o-iterations 200 # MCTS vs a weaker MCTS
python -m connect4.play_q1 --x human                   # you play X against MCTS
```

**Run the experiments for the report** (about 15–20 minutes; writes `results/`):

```
python -m connect4.experiments_q1
python -m connect4.experiments_q1 --runs 3 --games 4 --out output   # quick version
```

## Running Questions 2-4: propositional logic

```
python -m logic.logic_q234
```

This prints the truth tables for Q2 and Q4, the model counts for Q3, every CNF step for both sides of the Q4 sentence, and the resolution proof.

## Assumptions

### Question 1
1. **Board:** 6 rows by 7 columns. X always moves first. A move is a column number from 0 to 6.
2. **Selection utility:** `U/N + c·sqrt(ln N_parent / N) + w·h/(N+1)`. The first two terms are UCB1 (the *playout* part). `h` is the *objective* part, computed from the rules (see answers.md). An unvisited child is always tried first.
3. **Expansion:** a leaf gets its best `x` children, ranked by the objective value. The rest of the moves at that node are never searched.
4. **Tree height:** a node at depth `max_depth` is never expanded. Random playouts start from it.
5. **Playout result:** each node counts a win as 1, a draw as 0.5 and a loss as 0, for the player who made the move into that node.
6. **Final move:** the root child with the most playouts, as in Fig. 5.11 (ties go to the higher win rate).

### Questions 2-4
1. "Neither" means satisfiable but not valid.
2. Q3 counts models over all four symbols A, B, C, D, even if a sentence uses fewer of them.
