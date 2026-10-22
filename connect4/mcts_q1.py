# ------------------------------------------------------------------------
# mcts_q1.py
# Question 1 - Connect Four move generator using Monte Carlo tree search,
# AIMA 4th ed., Figure 5.11:
#
#   function MONTE-CARLO-TREE-SEARCH(state) returns an action
#     tree <- NODE(state)
#     while IS-TIME-REMAINING() do
#       leaf   <- SELECT(tree)
#       child  <- EXPAND(leaf)
#       result <- SIMULATE(child)
#       BACK-PROPAGATE(result, child)
#     return the move in ACTIONS(state) whose node has highest number of playouts
#
# What the assignment asks for, and where it is in this file:
#   selection   select() picks the child with the highest selection_utility(),
#               which adds a PLAYOUT part (win rate stored from earlier
#               playouts + UCB1 exploration bonus) and an OBJECTIVE part
#               (evaluate() from game_q1.py, computed from the rules).
#   expansion   expand() adds the best `expand_width` (= x) children of a leaf.
#   simulation  simulate() plays random moves to the end of the game. The
#               tree stops growing at `max_depth` (the height of the tree);
#               nodes at that level are simulated from, never expanded.
#   repeat      the main loop runs `iterations` times (configurable).
#
# Run from the project root:
#   python -m connect4.mcts_q1                               (empty board)
#   python -m connect4.mcts_q1 --moves 3 3 4 4 5 --iterations 2000 --seed 1
# ------------------------------------------------------------------------

import argparse
import math
import random
from dataclasses import dataclass

from connect4.game_q1 import ConnectFour, evaluate


@dataclass
class MCTSConfig:
    # All the settings we experiment with in the report.
    iterations: int = 1000        # how many times the 4 steps are repeated
    expand_width: int = 7         # x = children added per expansion (7 = all moves)
    max_depth: int | None = None  # height of the tree (None = no limit)
    c: float = 1.4                # weight of the UCB1 exploration bonus
    w: float = 1.0                # weight of the objective (rules) part
    bias: str = "decay"           # "decay": w*h/(N+1)   "constant": w*h
    seed: int | None = None       # random seed for the playouts (None = random)


class MCTNode:
    # A node of the Monte Carlo search tree (aima-python calls it MCT_Node).
    #   U  total reward of the playouts through this node, counted for the
    #      player who MADE the move into this node (1 win, 0.5 draw, 0 loss)
    #   N  number of playouts through this node
    #   h  objective value of the node's state for that same player
    def __init__(self, state, parent=None, move=None, mover=None, h=0.0):
        self.state = state
        self.parent = parent
        self.move = move            # column played to reach this node
        self.mover = mover          # player who played that move
        self.h = h
        self.U = 0.0
        self.N = 0
        self.children = []          # empty until the node is expanded
        self.depth = 0 if parent is None else parent.depth + 1

    def __repr__(self):
        return f"<MCTNode move={self.move} U={self.U} N={self.N} h={self.h:.2f}>"


def selection_utility(node, c=1.4, w=1.0, bias="decay"):
    # The utility function used in SELECT.
    #
    #   utility(n) = U(n)/N(n)                                  playout part
    #              + c * sqrt( ln N(parent) / N(n) )            exploration (UCB1)
    #              + w * h(n) / (N(n) + 1)                      objective part
    #
    # The first two terms are the UCB1 formula from the book. The objective
    # term guides the search while a node has few playouts; it shrinks as
    # N grows, so with many playouts the real results take over
    # ("progressive bias"). With bias="constant" it never shrinks.
    if node.N == 0:
        return math.inf             # always try an unvisited child first
    playout = node.U / node.N
    exploration = c * math.sqrt(math.log(node.parent.N) / node.N)
    objective = w * node.h / (node.N + 1) if bias == "decay" else w * node.h
    return playout + exploration + objective


def monte_carlo_tree_search(game, state, config=None, rng=None):
    # Returns (best move, root of the search tree).
    config = config or MCTSConfig()
    rng = rng or random.Random(config.seed)

    def select(node):
        # SELECT: walk down the tree, always taking the child with the
        # highest utility, until we reach a node without children (a leaf).
        while node.children:
            node = max(node.children,
                       key=lambda n: selection_utility(n, config.c, config.w, config.bias))
        return node

    def expand(leaf):
        # EXPAND: add up to x children to the leaf and return one of them.
        # The tree does not grow past max_depth, and a finished game has
        # no children, so in those cases the leaf itself is simulated.
        if game.is_terminal(leaf.state):
            return leaf
        if config.max_depth is not None and leaf.depth >= config.max_depth:
            return leaf

        player = game.to_move(leaf.state)
        candidates = []
        for move in game.actions(leaf.state):
            s = game.result(leaf.state, move)
            candidates.append(MCTNode(s, leaf, move, player, evaluate(game, s, player)))

        # Keep the x best children by the objective value (rules of the game).
        # Python's sort is stable, so equal values keep column order.
        candidates.sort(key=lambda n: n.h, reverse=True)
        leaf.children = candidates[:config.expand_width]
        return leaf.children[0]     # unvisited, and the most promising

    def simulate(node):
        # SIMULATE: random playout policy - both players pick uniformly
        # random legal moves until the game ends. Returns the winner
        # ("X", "O") or None for a draw.
        s = node.state
        while not game.is_terminal(s):
            s = game.result(s, rng.choice(game.actions(s)))
        return s.winner

    def back_propagate(winner, node):
        # BACK-PROPAGATE: update every node from `node` up to the root.
        # Each node is scored for the player who moved into it.
        while node is not None:
            node.N += 1
            if winner is None:
                node.U += 0.5
            elif winner == node.mover:
                node.U += 1
            node = node.parent

    # tree <- NODE(state)
    root = MCTNode(state)
    if game.is_terminal(state):
        return None, root

    # while IS-TIME-REMAINING() do   (here: a fixed number of iterations)
    for _ in range(config.iterations):
        leaf = select(root)
        child = expand(leaf)
        result = simulate(child)
        back_propagate(result, child)

    # return the move whose node has the highest number of playouts
    # (ties are broken by the better win rate)
    best = max(root.children, key=lambda n: (n.N, n.U / n.N if n.N else 0))
    return best.move, root


class MCTSPlayer:
    # Small wrapper so MCTS can be used as a player in a game loop.
    def __init__(self, config=None, name=None):
        self.config = config or MCTSConfig()
        self.rng = random.Random(self.config.seed)
        self.name = name or "MCTS"
        self.last_root = None       # kept so the search can be inspected

    def __call__(self, game, state):
        move, self.last_root = monte_carlo_tree_search(game, state, self.config, self.rng)
        return move


class RandomPlayer:
    # Baseline opponent: plays a uniformly random legal move.
    def __init__(self, seed=None, name="Random"):
        self.rng = random.Random(seed)
        self.name = name

    def __call__(self, game, state):
        return self.rng.choice(game.actions(state))


def root_stats(root):
    # Table of what the search learned about each move at the root.
    rows = []
    for n in sorted(root.children, key=lambda n: n.move):
        rows.append({"move": n.move, "N": n.N, "win_rate": n.U / n.N if n.N else 0.0, "h": n.h})
    return rows


def tree_size(root):
    # Number of nodes and the deepest level of the tree (for the report).
    count, deepest, stack = 0, 0, [root]
    while stack:
        n = stack.pop()
        count += 1
        deepest = max(deepest, n.depth)
        stack.extend(n.children)
    return count, deepest


def main():
    parser = argparse.ArgumentParser(description="Connect Four move generator (MCTS, AIMA Fig 5.11)")
    parser.add_argument("--moves", type=int, nargs="*", default=[], help="columns played so far, e.g. 3 3 4")
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--width", type=int, default=7, help="expansion width x (1-7)")
    parser.add_argument("--depth", type=int, default=None, help="max tree height (default: no limit)")
    parser.add_argument("--c", type=float, default=1.4, help="exploration weight")
    parser.add_argument("--w", type=float, default=1.0, help="objective weight")
    parser.add_argument("--bias", choices=["decay", "constant"], default="decay")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    game = ConnectFour()
    state = game.play(args.moves)
    config = MCTSConfig(args.iterations, args.width, args.depth, args.c, args.w, args.bias, args.seed)

    print(game.display(state))
    print(f"\n{state.to_move} to move. {config}\n")
    move, root = monte_carlo_tree_search(game, state, config)
    if move is None:
        print("The game is over.")
        return

    print(f"{'move':>4} {'playouts':>9} {'win rate':>9} {'objective':>10}")
    for row in root_stats(root):
        print(f"{row['move']:>4} {row['N']:>9} {row['win_rate']:>9.3f} {row['h']:>10.3f}")
    nodes, deepest = tree_size(root)
    print(f"\nTree: {nodes} nodes, deepest level {deepest}")
    print(f"Chosen move: column {move}")


if __name__ == "__main__":
    main()
