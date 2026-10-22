# DPS970 – Activity 2: Written Answers and Report

| | |
|---|---|
| **Name** | Trung Hieu Duong |
| **Student ID** | 160982237 |
| **Course** | DPS970 – AI for Software Developers |
| **Due date** | October 22, 2026 |

---

## Question 1 – Connect Four Move Generator (Monte Carlo Tree Search)

### 1.1 Design

The move generator follows **MONTE-CARLO-TREE-SEARCH** from AIMA Fig. 5.11. The code in `connect4/mcts_q1.py` uses the same four steps and names:

```
function MONTE-CARLO-TREE-SEARCH(state) returns an action
  tree ← NODE(state)
  while IS-TIME-REMAINING() do          →  for _ in range(config.iterations)
    leaf   ← SELECT(tree)               →  select(root)
    child  ← EXPAND(leaf)               →  expand(leaf)
    result ← SIMULATE(child)            →  simulate(child)
    BACK-PROPAGATE(result, child)       →  back_propagate(result, child)
  return the move in ACTIONS(state) whose node has highest number of playouts
```

The game itself (`connect4/game_q1.py`) uses the book's formal game definition: `initial`, `to_move`, `actions`, `result`, `is_terminal` and `utility`. A state is a 6 × 7 board stored as an immutable tuple, so the tree nodes can share states safely.

| Assignment requirement | How it is done |
|---|---|
| **Selection** with a utility function that has a *playout* part and an *objective* part | `selection_utility(n) = U(n)/N(n) + c·sqrt(ln N(parent)/N(n)) + w·h(n)/(N(n)+1)`. See 1.2. |
| **Expansion**: at each level, select *x* nodes to expand | `expand()` creates every child of the leaf, ranks them by the objective value `h`, and keeps the best **x** (`expand_width`). x = 7 keeps all moves. |
| **Simulation** at a fixed level of the tree, with a random playout policy | The tree never grows below `max_depth` (the height of the tree). From the selected node, `simulate()` plays **uniformly random** legal moves for both players until the game ends. |
| Repeat a **configurable** number of times | `iterations` (the book's IS-TIME-REMAINING). All settings are in `MCTSConfig` and on the command line. |

**Back-propagation.** Each node stores `U` (total reward) and `N` (number of playouts). Rewards are counted for the player **who made the move into that node**: a win is 1, a draw is 0.5 and a loss is 0. Because of this, `U/N` is always "how good this move was for the player who chose it", and SELECT can simply take the maximum at every level, for both players.

### 1.2 The utility function

```
utility(n) =  U(n) / N(n)                         ← playout part: win rate stored from earlier playouts
           +  c · sqrt( ln N(parent) / N(n) )      ← playout part: UCB1 exploration bonus
           +  w · h(n) / (N(n) + 1)                ← objective part: evaluation from the rules
```

- The first two terms are **UCB1** from the book. They use only results from earlier playouts.
- `h(n)` is the **objective** part, `evaluate()` in `game_q1.py`. It is computed only from the rules of Connect Four, for the player who moved into `n`, and it is between −1 and +1:
  - finished game: +1 win, −1 loss, 0 draw;
  - the player to move can complete four in a row right now: ±0.9;
  - otherwise, the board has **69 windows** of four cells in a line. A window that holds pieces of only one player is worth 1 / 4 / 16 points for 1 / 2 / 3 pieces. A window with pieces of both players can never be won, so it is worth 0. Each piece in the centre column adds 3 points (the centre is part of the most windows). The total is scaled with `0.8 · tanh(score / 40)`.
- Dividing by `N + 1` makes the objective part **decay**. While a node has few playouts, the rules guide the search. Once it has many, the real playout results take over. This idea is called *progressive bias*. The experiments also try a **constant** objective (`w · h`, no decay) and `w = 0` (pure UCB1).
- An unvisited child gets utility ∞, so it is tried first. Children are stored in objective order, so the most promising unvisited child is tried first.

### 1.3 Experiment setup

`python -m connect4.experiments_q1` produced every number below (raw data: `results/experiments_q1.csv`).

- **Base settings:** 200 iterations, x = 7, no depth limit, c = 1.4, w = 1, decaying bias. Each experiment changes **one** setting.
- The base uses only 200 iterations on purpose. With thousands of iterations almost every setting plays the same moves, which hides the differences.
- **Test positions** (`tests/positions_q1.json`, checked with a separate minimax solver):
  - **8 tactical positions** with a known correct answer: win horizontally, vertically or diagonally; block horizontally, vertically or diagonally; win instead of blocking; and avoid a move that lets the opponent win on top of it.
  - **3 quiet positions** with no single correct move: the empty board, after X 3 / O 3, and a midgame position.
- Each configuration was run **10 times** (seeds 0–9) on each of the 11 positions, so 110 searches per configuration.
- **Measures:**
  - *Tactical correct*: % of the 80 tactical searches that chose a correct move.
  - *Same-move agreement*: on the quiet positions, the share of the 10 runs that chose the most common move (100% = always the same move, 10% = all different).
  - *Move distributions*, written `move:count`. For example, `3:8 4:2` means column 3 eight times and column 4 twice.
  - *Time per search*, *tree size* and *deepest level of the tree*.
  - *Tournaments*: 20 full games between two configurations, with the first player alternating.

### 1.4 Results

#### A. Number of cycles (iterations)

| Setting | Tactical correct | Same-move agreement (quiet) | Empty board | Opening (3,3) | Midgame | ms / search | Tree nodes | Deepest level |
|---|---|---|---|---|---|---|---|---|
| iterations=25 | 73.8% | 50.0% | 3:5 2:2 4:1 1:1 0:1 | 3:4 0:2 1:2 5:1 6:1 | 3:6 4:2 6:1 2:1 | 9 | 161 | 3.0 |
| iterations=50 | 85.0% | 46.7% | 3:4 2:2 4:2 5:1 6:1 | 3:3 0:2 1:2 4:2 6:1 | 3:7 4:2 5:1 | 17 | 314 | 3.8 |
| iterations=100 | 100.0% | 53.3% | 3:5 2:2 6:1 4:1 5:1 | 3:3 1:2 4:2 0:1 2:1 6:1 | 3:8 4:1 1:1 | 42 | 585 | 4.0 |
| iterations=200 | 100.0% | 63.3% | 3:8 2:1 5:1 | 1:2 0:2 3:2 6:2 2:1 4:1 | 3:9 2:1 | 84 | 1082 | 4.7 |
| iterations=500 | 100.0% | 73.3% | 3:7 1:1 6:1 4:1 | 4:6 2:4 | 3:9 4:1 | 203 | 2492 | 5.4 |
| iterations=1000 | 100.0% | 73.3% | 3:7 2:2 1:1 | 2:5 4:5 | 3:10 | 400 | 4829 | 6.0 |
| iterations=2000 | 100.0% | 83.3% | 3:8 2:2 | 4:7 2:3 | 3:10 | 786 | 9222 | 6.4 |

- **Accuracy** grows with the number of cycles. With 25 or 50 iterations the generator **misses blocks** (74% and 85% correct). From 100 iterations on, it is always correct. All the misses were *block* positions. The *win* positions were correct even at 25 iterations, because the winning child is a finished game that returns a win on every playout.
- **Consistency** also grows: agreement on the quiet positions rises from about 50% to 83%. With more playouts the win-rate estimates have less noise, so the same move is picked more often. The midgame position reaches 10/10 from 1000 iterations on.
- **Cost** grows in a straight line with the iterations (about 0.4 ms per cycle). The tree gets bigger (9,222 nodes at 2000) and deeper (6.4 levels).

#### B. Utility function

| Setting | Tactical correct | Same-move agreement (quiet) | Empty board | Opening (3,3) | Midgame | ms / search | Tree nodes | Deepest level |
|---|---|---|---|---|---|---|---|---|
| UCB1 only (w=0) | 100.0% | 53.3% | 3:8 5:1 4:1 | 6:3 4:3 3:2 2:2 | 3:5 5:3 1:2 | 83 | 1109 | 4.5 |
| w=0.5, decaying | 98.8% | 50.0% | 3:4 4:2 2:2 6:1 1:1 | 4:5 2:2 3:2 1:1 | 3:6 2:3 1:1 | 90 | 1093 | 4.6 |
| w=1, decaying (base) | 100.0% | 63.3% | 3:8 2:1 5:1 | 1:2 0:2 3:2 6:2 2:1 4:1 | 3:9 2:1 | 99 | 1082 | 4.7 |
| w=2, decaying | 100.0% | 66.7% | 3:8 4:1 2:1 | 4:3 5:2 3:2 0:1 6:1 2:1 | 3:9 1:1 | 85 | 1080 | 4.9 |
| w=5, decaying | 100.0% | 73.3% | 3:7 2:1 4:1 0:1 | 3:5 4:2 5:1 6:1 2:1 | 3:10 | 94 | 1091 | 5.4 |
| w=1, constant | 100.0% | 86.7% | 3:9 4:1 | 3:7 2:2 4:1 | 3:10 | 80 | 1000 | 5.0 |
| c=0.5 (less exploration) | 100.0% | 63.3% | 3:4 4:3 2:2 5:1 | 2:5 5:2 3:1 6:1 1:1 | 3:10 | 81 | 990 | 5.7 |
| c=2.5 (more exploration) | 100.0% | 63.3% | 3:7 2:2 4:1 | 3:5 4:3 5:1 1:1 | 3:7 2:2 6:1 | 85 | 1170 | 4.2 |

- All the utility functions find the tactical moves at 200 iterations (one miss in 80 searches for w = 0.5). The differences show up in **consistency** and in **full games**.
- **Adding the objective part helps.** Pure UCB1 (w = 0) has 53% agreement. With w = 1, 2 and 5 it is 63%, 67% and 73%, so agreement rises as *w* grows. In the tournament, **w = 1 beat pure UCB1 12–6** (2 draws).
- **Decaying vs constant bias.** The constant objective (`w·h`, never shrinking) had the **highest agreement (86.7%)**, because the rules keep deciding no matter what the playouts say. The cost is that the playouts can never overrule a wrong evaluation. That is why the decaying version is the default.
- **Exploration constant c.** The value of c did not change the overall agreement (63% for both). It did change *which* moves were chosen. c = 0.5 spends playouts on a few moves and builds a deeper, narrower tree (5.7 levels). c = 2.5 spreads playouts across all moves (4.2 levels, more nodes).

#### C. Expansion nodes (x)

| Setting | Tactical correct | Same-move agreement (quiet) | Empty board | Opening (3,3) | Midgame | ms / search | Tree nodes | Deepest level |
|---|---|---|---|---|---|---|---|---|
| x=1 | 100.0% | 100.0% | 3:10 | 3:10 | 3:10 | 8 | 11 | 10.4 |
| x=2 | 100.0% | 100.0% | 3:10 | 2:10 | 3:10 | 59 | 224 | 9.9 |
| x=3 | 100.0% | 76.7% | 3:8 2:1 4:1 | 2:6 3:3 4:1 | 3:9 4:1 | 71 | 400 | 7.2 |
| x=5 | 100.0% | 66.7% | 3:6 1:2 2:2 | 4:5 2:3 1:2 | 3:9 5:1 | 83 | 731 | 5.4 |
| x=7 | 100.0% | 63.3% | 3:8 2:1 5:1 | 1:2 0:2 3:2 6:2 2:1 4:1 | 3:9 2:1 | 82 | 1082 | 4.7 |

- **Small x makes the generator consistent and fast.** x = 1 or x = 2 give 100% agreement. x = 1 turns MCTS into "follow the best move by the rules". The tree is a single line (11 nodes) that reaches the end of the game, so it takes only 8 ms. Its moves are exactly what the objective function says, so they are only as good as the objective function.
- **Larger x is more open but noisier.** Agreement falls to 63% at x = 7, because 200 playouts are shared among more moves.
- **x = 3 beat x = 7 in full games (12–5, 3 draws).** With few iterations, pruning weak moves and searching the remaining moves more deeply (7.2 vs 4.7 levels) is worth more than keeping every move. The risk is that a good move the objective ranks low is never searched.

#### D. Height of the tree

| Setting | Tactical correct | Same-move agreement (quiet) | Empty board | Opening (3,3) | Midgame | ms / search | Tree nodes | Deepest level |
|---|---|---|---|---|---|---|---|---|
| max_depth=1 | 87.5% | 50.0% | 3:4 2:2 0:1 5:1 1:1 4:1 | 2:4 3:3 4:2 5:1 | 3:7 2:1 1:1 4:1 | 19 | 8 | 1.0 |
| max_depth=2 | 96.2% | 53.3% | 2:4 3:4 5:2 | 2:4 4:2 1:2 5:1 3:1 | 3:8 4:1 1:1 | 22 | 54 | 2.0 |
| max_depth=3 | 100.0% | 50.0% | 3:6 4:2 1:1 0:1 | 2:2 4:2 1:2 0:1 3:1 5:1 6:1 | 3:7 4:2 1:1 | 35 | 360 | 3.0 |
| max_depth=5 | 100.0% | 63.3% | 3:8 2:1 5:1 | 1:2 0:2 3:2 6:2 2:1 4:1 | 3:9 2:1 | 81 | 1082 | 4.7 |
| max_depth=None | 100.0% | 63.3% | 3:8 2:1 5:1 | 1:2 0:2 3:2 6:2 2:1 4:1 | 3:9 2:1 | 81 | 1082 | 4.7 |

- **A short tree misses blocks.** With max_depth = 1 the tree has only the 7 root moves, and every move is judged only by random playouts: 87.5% correct. With max_depth = 2: 96%. From max_depth = 3 on: 100%. See 1.5 for why.
- **A taller tree plays better.** **max_depth = 2 lost to no limit 7–13.**
- max_depth = 5 gave *exactly* the same results as no limit. With 200 iterations the tree never needed to grow past 5 levels in these runs, so the limit had no effect.

#### E. Repeatability (base settings)

| Position | Same seed (7) run 10 times | Seeds 0-9 |
|---|---|---|
| empty_board | 2:10 | 3:8 2:1 5:1 |
| opening_2 | 3:10 | 1:2 0:2 3:2 6:2 2:1 4:1 |
| midgame | 3:10 | 3:9 2:1 |
| block_diagonal | 4:10 | 4:10 |

#### F. Tournaments (20 games each, first player alternates)

| Match (A vs B) | A wins | B wins | Draws |
|---|---|---|---|
| base vs Random | 20 | 0 | 0 |
| w=1 vs UCB1 only (w=0) | 12 | 6 | 2 |
| x=3 vs x=7 | 12 | 5 | 3 |
| max_depth=2 vs no limit | 7 | 13 | 0 |
| 1000 vs 200 iterations | 16 | 4 | 0 |

- MCTS beat the random player in **all 20 games**.
- The other results agree with the tables: more iterations (16–4), the objective part (12–6) and a taller tree (13–7) all make the generator stronger. Moderate pruning (x = 3) helps at this low budget.

### 1.5 Analysis and reflection

**Does the simulator always generate the same move?**

**It depends on the random seed and on the position.**

1. **Same seed → always the same move.** The only randomness in the program is the playout policy, and it uses a seeded random number generator (`random.Random(seed)`). With the same seed, every playout, every U/N value and the final move are identical (table E, second column, and the test `test_same_seed_gives_the_same_move_and_statistics`). This does **not** mean the move is the best one. With seed 7, the empty board gives column 2 every time, while most other seeds give column 3.
2. **Different seeds → the same move only when the position forces it.** In tactical positions (win now, block now) every seed gives the same correct move (block_diagonal: 10/10). In quiet positions the move changes from seed to seed. After X 3, O 3, the 10 seeds chose **six different columns** at 200 iterations.

**What causes the differences?**

- **Random playouts are a sample, not an exact value.** A move's win rate after 30 playouts has a standard error of roughly ±9 percentage points. In quiet positions the real difference between the top moves is smaller than that, so the noise decides. More iterations reduce the noise (agreement 50% → 83% in A).
- **Several moves are really equally good.** The board is symmetric. On the empty board, columns 2 and 4 are mirror images, and so are 1 and 5, and 0 and 6. After (3,3), with 1000–2000 iterations the choices split only between **2 and 4** (`2:5 4:5`, `4:7 2:3`): the generator found the two best moves, but they have the *same* true value, so the noise picks between them. A different move here is not a mistake.
- **Random opponents in the playouts are too forgiving.** This explains the missed blocks. If X does not block, O wins only if the *random* playout happens to choose the one winning column (about a 1 in 7 chance). So a non-blocking move can still get a good win rate from a few playouts. MCTS only "sees" the threat when the tree grows one level deeper, where SELECT makes O choose its winning reply on purpose. That is why few iterations (A) and a short tree (D, max_depth = 1) miss blocks, while a deeper tree does not.
- **Exploration (c)** decides how evenly the playouts are spread across moves, which changes which move ends up with the most playouts.

**What causes the similarities?**

- **Forced moves.** A winning move is a finished game, so it returns a win on every playout. A block is the only move that does not lose in the tree. Every configuration with enough iterations agrees on these.
- **The objective part.** The rules-based evaluation adds the same value on every run, whatever the seed, so a larger or constant *w* pulls every run towards the same move (agreement 53% → 87% in B).
- **Pruning (small x).** With x = 1 or 2, the objective function decides which moves exist in the tree, so all runs agree (100%). They agree because the search is less random, not because the moves are proven better.
- **Many iterations.** By the law of large numbers, the win rates converge to the same values, so different seeds agree more (the midgame position is 10/10 from 1000 iterations on).
- **Deterministic tie-breaking.** Children are ordered by the objective value, and ties keep column order. So when two moves have equal counts, every run breaks the tie the same way.

**Overall.** MCTS picks a move by **sampling**, so its choice is a random variable. The settings control how much it varies. More cycles and a taller tree make it **more accurate**. A stronger objective weight and smaller x make it **more consistent and faster**, but they rely more on the evaluation function and less on the playouts. The best trade-off we found for this budget was the decaying objective bias (w = 1) with moderate pruning (x = 3) and as many iterations as time allows.

One improvement would be a smarter playout policy that always takes an immediate win and blocks an immediate loss. This would fix the "forgiving random opponent" problem, but the assignment asks for a random playout policy, so we kept it random.

---

## Question 2 – Propositional Logic: Satisfiability

A sentence is **valid** if it is true in every model, **unsatisfiable** if it is true in no model, and **neither** if it is true in some models but not all (satisfiable but not valid).

### a) Smoke ⇒ Fire — **neither** (satisfiable, but not valid)

**Truth table**

| Smoke | Fire | Smoke ⇒ Fire |
|:-:|:-:|:-:|
| T | T | T |
| T | F | **F** |
| F | T | T |
| F | F | T |

The sentence is true in 3 models, so it is **satisfiable**. It is false when Smoke = T and Fire = F, so it is **not valid**.

**Equivalence rules:** Smoke ⇒ Fire ≡ ¬Smoke ∨ Fire (implication elimination). This is one clause with two different symbols and no complementary pair (like P ∨ ¬P), so it can be made false (Smoke = T, Fire = F) and it can be made true (Smoke = F). This confirms **neither**.

### b) ((Smoke ∧ Heat) ⇒ Fire) ⇔ ((Smoke ⇒ Fire) ∨ (Heat ⇒ Fire)) — **valid**

**Equivalence rules**

Left side:
1. (Smoke ∧ Heat) ⇒ Fire
2. ≡ ¬(Smoke ∧ Heat) ∨ Fire  (implication elimination)
3. ≡ ¬Smoke ∨ ¬Heat ∨ Fire  (De Morgan)

Right side:
1. (Smoke ⇒ Fire) ∨ (Heat ⇒ Fire)
2. ≡ (¬Smoke ∨ Fire) ∨ (¬Heat ∨ Fire)  (implication elimination)
3. ≡ ¬Smoke ∨ ¬Heat ∨ Fire ∨ Fire  (associativity, commutativity of ∨)
4. ≡ ¬Smoke ∨ ¬Heat ∨ Fire  (idempotence: Fire ∨ Fire ≡ Fire)

Both sides are the same sentence α, so the whole sentence is α ⇔ α, which is true in every model. It is **valid**.

**Truth table** (L = left side, R = right side)

| Smoke | Heat | Fire | L: (S∧H)⇒F | S⇒F | H⇒F | R: (S⇒F)∨(H⇒F) | L ⇔ R |
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| T | T | T | T | T | T | T | **T** |
| T | T | F | F | F | F | F | **T** |
| T | F | T | T | T | T | T | **T** |
| T | F | F | T | F | T | T | **T** |
| F | T | T | T | T | T | T | **T** |
| F | T | F | T | T | F | T | **T** |
| F | F | T | T | T | T | T | **T** |
| F | F | F | T | T | T | T | **T** |

L and R are false in exactly the same row (Smoke = T, Heat = T, Fire = F), so L ⇔ R is true in all 8 rows. **Valid.**

(Note: the sentence is valid, but this is a little surprising in English. "Smoke and heat together cause fire" is equivalent to "smoke causes fire, or heat causes fire". That is because both sides are false only when Smoke and Heat are true and Fire is false.)

---

## Question 3 – Models

With four symbols A, B, C, D there are 2⁴ = **16** possible models. A model of a sentence is one of those 16 assignments in which the sentence is true.

### a) B ∨ C — **12 models**

B ∨ C is false only when B = F **and** C = F. A and D do not appear, so each can be T or F: 2 × 2 = 4 assignments make the sentence false.
**16 − 4 = 12 models.**

(Or: B ∨ C is true for 3 of the 4 (B, C) combinations, times 4 combinations of (A, D): 3 × 4 = 12.)

### b) (A ⇒ B) ∧ A ∧ ¬B ∧ C ∧ D — **0 models**

For the conjunction to be true, every part must be true:
- A must be T and ¬B means B must be F.
- Then A ⇒ B is T ⇒ F, which is **false**.

So no assignment can make all parts true. (Another way to see it: from A and A ⇒ B, Modus Ponens gives B, which contradicts ¬B.) The sentence is **unsatisfiable**, with **0 models**.

`python -m logic.logic_q234` checks both counts by enumerating all 16 models.

---

## Question 4 – Propositional Logic: Resolution

Sentence: **[(Food ⇒ Party) ∨ (Drinks ⇒ Party)] ⇒ [(Food ∧ Drinks) ⇒ Party]**

### a) Enumeration — **valid**

LHS = (Food ⇒ Party) ∨ (Drinks ⇒ Party), RHS = (Food ∧ Drinks) ⇒ Party.

| Food | Drinks | Party | Food⇒Party | Drinks⇒Party | LHS | Food∧Drinks | RHS | LHS ⇒ RHS |
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| T | T | T | T | T | T | T | T | **T** |
| T | T | F | F | F | F | T | F | **T** |
| T | F | T | T | T | T | F | T | **T** |
| T | F | F | F | T | T | F | T | **T** |
| F | T | T | T | T | T | F | T | **T** |
| F | T | F | T | F | T | F | T | **T** |
| F | F | T | T | T | T | F | T | **T** |
| F | F | F | T | T | T | F | T | **T** |

The sentence is true in all 8 models, so it is **valid** (and therefore also satisfiable). An implication is false only when LHS = T and RHS = F, and that never happens: in fact LHS and RHS have the same value in every row.

### b) Conversion to CNF

Steps (AIMA Section 7.5.2): 1. eliminate ⇔, 2. eliminate ⇒, 3. move ¬ inwards, 4. distribute ∨ over ∧.

**Left-hand side:** (Food ⇒ Party) ∨ (Drinks ⇒ Party)

| Step | Result |
|---|---|
| 1. eliminate ⇔ | no ⇔, so no change |
| 2. eliminate ⇒ (α ⇒ β ≡ ¬α ∨ β) | (¬Food ∨ Party) ∨ (¬Drinks ∨ Party) |
| 3. move ¬ inwards | ¬ is already only on symbols, so no change |
| 4. distribute / simplify | no ∧ inside an ∨, so only remove brackets (associativity) and the repeated Party (idempotence): **¬Food ∨ ¬Drinks ∨ Party** |

**Right-hand side:** (Food ∧ Drinks) ⇒ Party

| Step | Result |
|---|---|
| 1. eliminate ⇔ | no ⇔, so no change |
| 2. eliminate ⇒ | ¬(Food ∧ Drinks) ∨ Party |
| 3. move ¬ inwards (De Morgan) | (¬Food ∨ ¬Drinks) ∨ Party |
| 4. distribute / simplify | **¬Food ∨ ¬Drinks ∨ Party** |

**How this confirms (a):** both sides become the **same single clause**, α = ¬Food ∨ ¬Drinks ∨ Party. So the whole sentence is α ⇒ α ≡ ¬α ∨ α, which is true in every model. This matches the truth table, where the LHS and RHS columns are identical and the sentence is **valid**.

### c) Proof by resolution

To prove that a sentence S is valid, show that **¬S is unsatisfiable**: convert ¬S to CNF and derive the empty clause (PL-RESOLUTION with an empty KB and α = S).

¬S = ¬(LHS ⇒ RHS) ≡ ¬(¬LHS ∨ RHS) ≡ LHS ∧ ¬RHS

- LHS in CNF (from b): ¬Food ∨ ¬Drinks ∨ Party
- ¬RHS = ¬(¬Food ∨ ¬Drinks ∨ Party) ≡ Food ∧ Drinks ∧ ¬Party (De Morgan, double negation)

Clauses of ¬S:

| # | Clause | From |
|---|---|---|
| 1 | ¬Food ∨ ¬Drinks ∨ Party | LHS |
| 2 | Food | ¬RHS |
| 3 | Drinks | ¬RHS |
| 4 | ¬Party | ¬RHS |

Resolution steps:

| # | Resolve | On | Result |
|---|---|---|---|
| 5 | 1 and 4 | Party / ¬Party | ¬Food ∨ ¬Drinks |
| 6 | 5 and 2 | ¬Food / Food | ¬Drinks |
| 7 | 6 and 3 | ¬Drinks / Drinks | **{ }** (empty clause) |

The empty clause is derived, so ¬S is unsatisfiable, so **S is valid**. This agrees with (a) and (b).

`python -m logic.logic_q234` runs PL-RESOLUTION on the same clauses and prints this same 3-step proof. The tests in `tests/test_logic_q234.py` also check that resolution and the truth tables agree on every test sentence.
