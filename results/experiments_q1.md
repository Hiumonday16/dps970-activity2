# Question 1 - Experiment results

Base settings: `MCTSConfig(iterations=200, expand_width=7, max_depth=None, c=1.4, w=1.0, bias='decay', seed=None)`  
Each configuration: 10 runs (seeds 0-9) x 11 positions.  
Tactical positions (8): win_horizontal, win_vertical, win_diagonal, block_horizontal, block_vertical, block_diagonal, win_before_block, avoid_trap.  
Move distributions are written `move:count`, most common first.

## A. Number of cycles (iterations)

| Setting | Tactical correct | Same-move agreement (quiet) | Empty board | Opening (3,3) | Midgame | ms / search | Tree nodes | Deepest level |
|---|---|---|---|---|---|---|---|---|
| iterations=25 | 73.8% | 50.0% | 3:5 2:2 4:1 1:1 0:1 | 3:4 0:2 1:2 5:1 6:1 | 3:6 4:2 6:1 2:1 | 9 | 161 | 3.0 |
| iterations=50 | 85.0% | 46.7% | 3:4 2:2 4:2 5:1 6:1 | 3:3 0:2 1:2 4:2 6:1 | 3:7 4:2 5:1 | 17 | 314 | 3.8 |
| iterations=100 | 100.0% | 53.3% | 3:5 2:2 6:1 4:1 5:1 | 3:3 1:2 4:2 0:1 2:1 6:1 | 3:8 4:1 1:1 | 42 | 585 | 4.0 |
| iterations=200 | 100.0% | 63.3% | 3:8 2:1 5:1 | 1:2 0:2 3:2 6:2 2:1 4:1 | 3:9 2:1 | 84 | 1082 | 4.7 |
| iterations=500 | 100.0% | 73.3% | 3:7 1:1 6:1 4:1 | 4:6 2:4 | 3:9 4:1 | 203 | 2492 | 5.4 |
| iterations=1000 | 100.0% | 73.3% | 3:7 2:2 1:1 | 2:5 4:5 | 3:10 | 400 | 4829 | 6.0 |
| iterations=2000 | 100.0% | 83.3% | 3:8 2:2 | 4:7 2:3 | 3:10 | 786 | 9222 | 6.4 |

## B. Utility function

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

## C. Expansion nodes (x)

| Setting | Tactical correct | Same-move agreement (quiet) | Empty board | Opening (3,3) | Midgame | ms / search | Tree nodes | Deepest level |
|---|---|---|---|---|---|---|---|---|
| x=1 | 100.0% | 100.0% | 3:10 | 3:10 | 3:10 | 8 | 11 | 10.4 |
| x=2 | 100.0% | 100.0% | 3:10 | 2:10 | 3:10 | 59 | 224 | 9.9 |
| x=3 | 100.0% | 76.7% | 3:8 2:1 4:1 | 2:6 3:3 4:1 | 3:9 4:1 | 71 | 400 | 7.2 |
| x=5 | 100.0% | 66.7% | 3:6 1:2 2:2 | 4:5 2:3 1:2 | 3:9 5:1 | 83 | 731 | 5.4 |
| x=7 | 100.0% | 63.3% | 3:8 2:1 5:1 | 1:2 0:2 3:2 6:2 2:1 4:1 | 3:9 2:1 | 82 | 1082 | 4.7 |

## D. Height of the tree

| Setting | Tactical correct | Same-move agreement (quiet) | Empty board | Opening (3,3) | Midgame | ms / search | Tree nodes | Deepest level |
|---|---|---|---|---|---|---|---|---|
| max_depth=1 | 87.5% | 50.0% | 3:4 2:2 0:1 5:1 1:1 4:1 | 2:4 3:3 4:2 5:1 | 3:7 2:1 1:1 4:1 | 19 | 8 | 1.0 |
| max_depth=2 | 96.2% | 53.3% | 2:4 3:4 5:2 | 2:4 4:2 1:2 5:1 3:1 | 3:8 4:1 1:1 | 22 | 54 | 2.0 |
| max_depth=3 | 100.0% | 50.0% | 3:6 4:2 1:1 0:1 | 2:2 4:2 1:2 0:1 3:1 5:1 6:1 | 3:7 4:2 1:1 | 35 | 360 | 3.0 |
| max_depth=5 | 100.0% | 63.3% | 3:8 2:1 5:1 | 1:2 0:2 3:2 6:2 2:1 4:1 | 3:9 2:1 | 81 | 1082 | 4.7 |
| max_depth=None | 100.0% | 63.3% | 3:8 2:1 5:1 | 1:2 0:2 3:2 6:2 2:1 4:1 | 3:9 2:1 | 81 | 1082 | 4.7 |

## E. Repeatability (base settings)

| Position | Same seed (7) run 10 times | Seeds 0-9 |
|---|---|---|
| empty_board | 2:10 | 3:8 2:1 5:1 |
| opening_2 | 3:10 | 1:2 0:2 3:2 6:2 2:1 4:1 |
| midgame | 3:10 | 3:9 2:1 |
| block_diagonal | 4:10 | 4:10 |

## F. Tournaments (first player alternates every game)

| Match (A vs B) | A wins | B wins | Draws |
|---|---|---|---|
| base vs Random | 20 | 0 | 0 |
| w=1 vs UCB1 only (w=0) | 12 | 6 | 2 |
| x=3 vs x=7 | 12 | 5 | 3 |
| max_depth=2 vs no limit | 7 | 13 | 0 |
| 1000 vs 200 iterations | 16 | 4 | 0 |
