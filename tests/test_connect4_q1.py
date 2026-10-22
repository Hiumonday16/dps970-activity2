# ------------------------------------------------------------------------
# test_connect4_q1.py
# Automated tests for Question 1, part 1: the Connect Four game rules and
# the objective (rules-based) evaluation function.
# Run from the project root with:   pytest -v
# ------------------------------------------------------------------------

import json
from pathlib import Path

import pytest

from connect4.game_q1 import COLS, ROWS, WINDOWS, O, X, ConnectFour, cell, evaluate

# Test data: board positions written as the list of columns played.
POSITIONS = json.loads((Path(__file__).parent / "positions_q1.json").read_text())


@pytest.fixture
def game():
    return ConnectFour()


# ==================== 1. Formal definition of the game ===================

def test_initial_state(game):
    s = game.initial
    assert game.to_move(s) == X
    assert game.actions(s) == list(range(7))
    assert not game.is_terminal(s)
    assert len(s.board) == ROWS * COLS == 42


def test_pieces_fall_to_the_lowest_empty_cell(game):
    s = game.play([3, 3, 3])
    assert s.board[cell(0, 3)] == X
    assert s.board[cell(1, 3)] == O
    assert s.board[cell(2, 3)] == X
    assert s.heights[3] == 3


def test_players_take_turns(game):
    s = game.initial
    for expected in (X, O, X, O):
        assert game.to_move(s) == expected
        s = game.result(s, 0)


def test_result_does_not_change_the_old_state(game):
    s = game.initial
    game.result(s, 3)
    assert s.board == game.initial.board


def test_full_column_is_not_a_legal_move(game):
    s = game.play([0] * 6)
    assert 0 not in game.actions(s)
    with pytest.raises(ValueError):
        game.result(s, 0)


@pytest.mark.parametrize("moves", [
    [0, 0, 1, 1, 2, 2, 3],              # horizontal
    [0, 1, 0, 1, 0, 1, 0],              # vertical
    [0, 1, 1, 2, 2, 3, 2, 3, 3, 6, 3],  # diagonal /
    [6, 5, 5, 4, 4, 3, 4, 3, 3, 0, 3],  # diagonal \
], ids=["horizontal", "vertical", "diagonal_up", "diagonal_down"])
def test_four_in_a_row_wins(game, moves):
    s = game.play(moves)
    assert s.winner == X
    assert game.is_terminal(s)
    assert game.utility(s, X) == 1
    assert game.utility(s, O) == -1
    assert game.actions(s) == []        # no moves after the game is over


def test_three_in_a_row_is_not_a_win(game):
    s = game.play([0, 0, 1, 1, 2])
    assert s.winner is None
    assert not game.is_terminal(s)


def test_full_board_without_winner_is_a_draw(game):
    # Columns filled in pairs in this order give a full board with no four.
    order = [0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0,
             2, 3, 2, 3, 2, 3, 3, 2, 3, 2, 3, 2,
             4, 5, 4, 5, 4, 5, 5, 4, 5, 4, 5, 4,
             6, 6, 6, 6, 6, 6]
    s = game.play(order)
    assert s.n_moves == 42
    assert s.winner is None
    assert game.is_terminal(s)
    assert game.utility(s, X) == 0


def test_there_are_69_windows_of_four():
    assert len(WINDOWS) == 69


@pytest.mark.parametrize("p", [p for p in POSITIONS if p["name"].startswith("win")], ids=lambda p: p["name"])
def test_winning_moves_found(game, p):
    s = game.play(p["moves"])
    assert set(game.winning_moves(s)) == set(p["best"])


@pytest.mark.parametrize("p", [p for p in POSITIONS if p["name"].startswith("block")], ids=lambda p: p["name"])
def test_opponent_threats_found(game, p):
    # In the "block" positions the opponent's winning cell is the answer.
    s = game.play(p["moves"])
    opponent = O if s.to_move == X else X
    assert game.winning_moves(s, opponent) == p["best"]


# ==================== 2. Objective function ==============================

def test_evaluate_finished_game(game):
    s = game.play([0, 1, 0, 1, 0, 1, 0])
    assert evaluate(game, s, X) == 1.0
    assert evaluate(game, s, O) == -1.0


def test_evaluate_empty_board_is_even(game):
    assert evaluate(game, game.initial, X) == 0.0


def test_evaluate_is_zero_sum(game):
    # Good for one player = equally bad for the other.
    for p in POSITIONS:
        s = game.play(p["moves"])
        assert evaluate(game, s, X) == pytest.approx(-evaluate(game, s, O))


def test_evaluate_stays_between_minus_one_and_one(game):
    for p in POSITIONS:
        s = game.play(p["moves"])
        assert -1.0 <= evaluate(game, s, X) <= 1.0


def test_evaluate_prefers_the_centre(game):
    centre = game.result(game.initial, 3)
    edge = game.result(game.initial, 0)
    assert evaluate(game, centre, X) > evaluate(game, edge, X)


def test_evaluate_sees_an_immediate_win_for_the_player_to_move(game):
    # X to move and X can win now -> close to +1 for X
    s = game.play([0, 6, 1, 6, 2, 5])
    assert evaluate(game, s, X) == pytest.approx(0.9)


def test_evaluate_punishes_not_blocking(game):
    # After X ignores O's threat, the position is almost lost for X.
    s = game.play([6, 1, 6, 2, 0, 3])          # O threatens column 4
    blocked = game.result(s, 4)
    ignored = game.result(s, 6)
    assert evaluate(game, blocked, X) > evaluate(game, ignored, X)
    assert evaluate(game, ignored, X) == pytest.approx(-0.9)
