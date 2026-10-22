# ------------------------------------------------------------------------
# test_mcts_q1.py
# Automated tests for Question 1, part 2: the Monte Carlo tree search
# move generator (selection, expansion, simulation, back-propagation).
# Run from the project root with:   pytest -v
# ------------------------------------------------------------------------

import json
import math
from pathlib import Path

import pytest

from connect4.game_q1 import O, X, ConnectFour
from connect4.mcts_q1 import (MCTNode, MCTSConfig, MCTSPlayer, RandomPlayer, monte_carlo_tree_search,
                              root_stats, selection_utility, tree_size)
from connect4.play_q1 import play_game

# Test data: positions with the correct move(s) for the tactical ones.
POSITIONS = json.loads((Path(__file__).parent / "positions_q1.json").read_text())
TACTICAL = [p for p in POSITIONS if p["type"] == "tactical"]


@pytest.fixture
def game():
    return ConnectFour()


def all_nodes(root):
    stack, nodes = [root], []
    while stack:
        n = stack.pop()
        nodes.append(n)
        stack.extend(n.children)
    return nodes


# ==================== 1. Selection utility ===============================

def make_child(U, N, h, parent_N):
    parent = MCTNode(None)
    parent.N = parent_N
    child = MCTNode(None, parent, 0, X, h)
    child.U, child.N = U, N
    return child


def test_unvisited_node_is_tried_first():
    assert selection_utility(make_child(0, 0, -1.0, 10)) == math.inf


def test_w_zero_is_plain_ucb1():
    # UCB1 = U/N + c * sqrt(ln N(parent) / N)
    n = make_child(U=6, N=10, h=0.7, parent_N=50)
    expected = 6 / 10 + 1.4 * math.sqrt(math.log(50) / 10)
    assert selection_utility(n, c=1.4, w=0.0) == pytest.approx(expected)


def test_objective_part_decays_with_more_playouts():
    few = make_child(U=5, N=10, h=0.5, parent_N=100)
    many = make_child(U=50, N=100, h=0.5, parent_N=1000)
    bonus_few = selection_utility(few, w=1) - selection_utility(few, w=0)
    bonus_many = selection_utility(many, w=1) - selection_utility(many, w=0)
    assert bonus_few == pytest.approx(0.5 / 11)
    assert bonus_many == pytest.approx(0.5 / 101)


def test_constant_objective_does_not_decay():
    n = make_child(U=50, N=100, h=0.5, parent_N=1000)
    bonus = selection_utility(n, w=1, bias="constant") - selection_utility(n, w=0)
    assert bonus == pytest.approx(0.5)


def test_higher_objective_gives_higher_utility():
    good = make_child(U=5, N=10, h=0.8, parent_N=100)
    bad = make_child(U=5, N=10, h=-0.8, parent_N=100)
    assert selection_utility(good) > selection_utility(bad)


# ==================== 2. The search tree =================================

def test_returns_a_legal_move(game):
    s = game.play([3, 3, 2])
    move, _ = monte_carlo_tree_search(game, s, MCTSConfig(iterations=100, seed=0))
    assert move in game.actions(s)


@pytest.mark.parametrize("iterations", [1, 10, 250])
def test_number_of_cycles_is_respected(game, iterations):
    _, root = monte_carlo_tree_search(game, game.initial, MCTSConfig(iterations=iterations, seed=0))
    assert root.N == iterations


def test_visit_counts_add_up(game):
    # Every playout passes through exactly one child of each expanded node,
    # so a node's N = playouts that stopped at it + sum of its children's N.
    _, root = monte_carlo_tree_search(game, game.initial, MCTSConfig(iterations=300, seed=1))
    assert sum(c.N for c in root.children) == root.N
    for n in all_nodes(root):
        assert n.N >= sum(c.N for c in n.children)
        assert 0 <= n.U <= n.N


@pytest.mark.parametrize("x", [1, 2, 3, 7])
def test_expansion_adds_at_most_x_children(game, x):
    _, root = monte_carlo_tree_search(game, game.initial, MCTSConfig(iterations=200, expand_width=x, seed=0))
    assert len(root.children) == x
    assert all(len(n.children) <= x for n in all_nodes(root))


def test_expansion_keeps_the_best_children_by_objective(game):
    # With x=1 the only child of the empty board must be the centre column.
    _, root = monte_carlo_tree_search(game, game.initial, MCTSConfig(iterations=10, expand_width=1, seed=0))
    assert [c.move for c in root.children] == [3]


@pytest.mark.parametrize("depth", [1, 2, 4])
def test_tree_never_grows_past_max_depth(game, depth):
    _, root = monte_carlo_tree_search(game, game.initial, MCTSConfig(iterations=300, max_depth=depth, seed=0))
    _, deepest = tree_size(root)
    assert deepest == depth


def test_children_are_scored_for_the_player_who_moved(game):
    # X can win immediately with column 3: that child is a terminal win
    # for X, so every playout through it counts as a win (win rate 1.0).
    s = game.play([0, 6, 1, 6, 2, 5])
    _, root = monte_carlo_tree_search(game, s, MCTSConfig(iterations=200, seed=0))
    winning = next(c for c in root.children if c.move == 3)
    assert winning.mover == X
    assert winning.U == winning.N
    assert root_stats(root)[3]["win_rate"] == 1.0


def test_terminal_state_returns_no_move(game):
    s = game.play([0, 1, 0, 1, 0, 1, 0])
    move, root = monte_carlo_tree_search(game, s, MCTSConfig(iterations=50, seed=0))
    assert move is None
    assert root.children == []


def test_only_one_legal_move(game):
    # Fill columns 0-5 completely (no one wins), leaving only column 6.
    order = [0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0,
             2, 3, 2, 3, 2, 3, 3, 2, 3, 2, 3, 2,
             4, 5, 4, 5, 4, 5, 5, 4, 5, 4, 5, 4]
    s = game.play(order)
    assert game.actions(s) == [6]
    move, _ = monte_carlo_tree_search(game, s, MCTSConfig(iterations=30, seed=0))
    assert move == 6


# ==================== 3. Repeatability ===================================

def test_same_seed_gives_the_same_move_and_statistics(game):
    s = game.play([3, 3])
    config = MCTSConfig(iterations=200, seed=42)
    move1, root1 = monte_carlo_tree_search(game, s, config)
    move2, root2 = monte_carlo_tree_search(game, s, config)
    assert move1 == move2
    assert root_stats(root1) == root_stats(root2)


def test_different_seeds_give_different_playouts(game):
    s = game.play([3, 3])
    stats = {str(root_stats(monte_carlo_tree_search(game, s, MCTSConfig(iterations=200, seed=k))[1]))
             for k in range(5)}
    assert len(stats) > 1


# ==================== 4. Move quality ====================================

@pytest.mark.parametrize("p", TACTICAL, ids=lambda p: p["name"])
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_finds_the_correct_tactical_move(game, p, seed):
    s = game.play(p["moves"])
    move, _ = monte_carlo_tree_search(game, s, MCTSConfig(iterations=300, seed=seed))
    assert move in p["best"]


def test_opening_move_is_the_centre(game):
    move, _ = monte_carlo_tree_search(game, game.initial, MCTSConfig(iterations=2000, seed=0))
    assert move == 3


def test_mcts_beats_a_random_player(game):
    wins = 0
    for g in range(4):
        mcts = MCTSPlayer(MCTSConfig(iterations=100, seed=g))
        rand = RandomPlayer(seed=100 + g)
        if g % 2 == 0:
            wins += play_game(game, mcts, rand) == X
        else:
            wins += play_game(game, rand, mcts) == O
    assert wins == 4
