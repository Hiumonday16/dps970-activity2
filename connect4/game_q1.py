# ------------------------------------------------------------------------
# game_q1.py
# Question 1 - The game of Connect Four (6 rows x 7 columns).
#
# The game is written with the same interface as the book's formal
# definition of a game (AIMA 4th ed., Section 5.1) and the Game class
# in aima-python (games4e.py):
#
#   S0              initial            the empty board, X moves first
#   TO-MOVE(s)      to_move(s)         whose turn it is
#   ACTIONS(s)      actions(s)         the columns that are not full
#   RESULT(s, a)    result(s, a)       drop a piece into column a
#   IS-TERMINAL(s)  is_terminal(s)     four in a row, or the board is full
#   UTILITY(s, p)   utility(s, p)      +1 win, -1 loss, 0 draw for player p
#
# It also has the OBJECTIVE part of the MCTS utility function:
#   evaluate(s, p)  a score in [-1, +1] for player p, computed only from
#                   the rules of the game (lines of four that are still
#                   open, centre control, and immediate wins).
# ------------------------------------------------------------------------

import math

ROWS, COLS, CONNECT = 6, 7, 4
EMPTY, X, O = ".", "X", "O"


def other(player):
    # The opponent of a player.
    return O if player == X else X


def cell(row, col):
    # The board is stored as a flat tuple of 42 cells.
    # Row 0 is the BOTTOM row, so pieces "fall" towards row 0.
    return row * COLS + col


def _all_windows():
    # Every group of 4 cells in a straight line (a "window").
    # Connect Four has 69 of them: 24 horizontal, 21 vertical, 24 diagonal.
    windows = []
    for r in range(ROWS):
        for c in range(COLS):
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                end_r, end_c = r + dr * (CONNECT - 1), c + dc * (CONNECT - 1)
                if 0 <= end_r < ROWS and 0 <= end_c < COLS:
                    windows.append(tuple(cell(r + dr * k, c + dc * k) for k in range(CONNECT)))
    return windows


WINDOWS = _all_windows()


class GameState:
    # One position of the game. It is never changed after it is created
    # (RESULT always builds a new state), so states can be shared safely
    # between the nodes of the search tree.
    __slots__ = ("board", "heights", "to_move", "last_move", "winner", "n_moves")

    def __init__(self, board, heights, to_move, last_move=None, winner=None, n_moves=0):
        self.board = board          # tuple of 42 cells: ".", "X" or "O"
        self.heights = heights      # tuple of 7: number of pieces in each column
        self.to_move = to_move      # "X" or "O"
        self.last_move = last_move  # column of the last move (None at the start)
        self.winner = winner        # "X", "O" or None
        self.n_moves = n_moves      # number of pieces on the board

    def __eq__(self, other_state):
        return (self.board, self.to_move) == (other_state.board, other_state.to_move)

    def __hash__(self):
        return hash((self.board, self.to_move))

    def __repr__(self):
        return f"<GameState to_move={self.to_move} moves={self.n_moves} winner={self.winner}>"


class ConnectFour:
    def __init__(self):
        # S0: an empty board and X (the first player) to move.
        self.initial = GameState((EMPTY,) * (ROWS * COLS), (0,) * COLS, X)

    # ---------------- formal definition of the game ----------------------

    def to_move(self, state):
        return state.to_move

    def actions(self, state):
        # A move is a column number 0-6. A full column is not a legal move.
        if state.winner is not None:
            return []
        return [c for c in range(COLS) if state.heights[c] < ROWS]

    def result(self, state, col):
        # Drop a piece of the player to move into column `col`.
        # The piece lands on the lowest empty cell of that column (gravity).
        row = state.heights[col]
        if state.winner is not None or row >= ROWS:
            raise ValueError(f"illegal move: column {col}")
        player = state.to_move

        board = list(state.board)
        board[cell(row, col)] = player
        heights = list(state.heights)
        heights[col] += 1

        board = tuple(board)
        winner = player if self._makes_four(board, row, col, player) else None
        return GameState(board, tuple(heights), other(player), col, winner, state.n_moves + 1)

    def is_terminal(self, state):
        # The game ends when someone has four in a row or the board is full.
        return state.winner is not None or state.n_moves == ROWS * COLS

    def utility(self, state, player):
        # Final payoff for `player`: +1 win, -1 loss, 0 draw.
        if state.winner is None:
            return 0
        return 1 if state.winner == player else -1

    # ---------------- helpers --------------------------------------------

    @staticmethod
    def _makes_four(board, row, col, player):
        # Only lines through the piece just played can be new wins, so we
        # count matching pieces in both directions along each of 4 lines.
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            count = 1
            for sign in (1, -1):
                r, c = row + dr * sign, col + dc * sign
                while 0 <= r < ROWS and 0 <= c < COLS and board[r * COLS + c] == player:
                    count += 1
                    r, c = r + dr * sign, c + dc * sign
            if count >= CONNECT:
                return True
        return False

    def winning_moves(self, state, player=None):
        # Columns where `player` (default: the player to move) would complete
        # four in a row if it were their turn. Used by the objective function.
        player = player or state.to_move
        moves = []
        for col in range(COLS):
            row = state.heights[col]
            if row < ROWS:
                board = list(state.board)
                board[cell(row, col)] = player
                if self._makes_four(board, row, col, player):
                    moves.append(col)
        return moves

    def play(self, moves, state=None):
        # Plays a list of columns, e.g. [3, 3, 4] -> X in col 3, O in col 3, X in col 4.
        state = state or self.initial
        for col in moves:
            state = self.result(state, col)
        return state

    def display(self, state):
        # Text picture of the board, top row first.
        lines = [" ".join(state.board[cell(r, c)] for c in range(COLS)) for r in reversed(range(ROWS))]
        lines.append(" ".join(str(c) for c in range(COLS)))
        return "\n".join(lines)


# ------------------------------------------------------------------------
# OBJECTIVE part of the utility function (from the rules of the game)
# ------------------------------------------------------------------------

# Points for a window that only contains our pieces (index = how many).
# A window with pieces of BOTH players can never become four in a row,
# so it is worth nothing to either side.
WINDOW_POINTS = (0, 1, 4, 16, 0)
CENTRE_POINTS = 3       # per piece in the centre column (it is in the most windows)
SCALE = 40.0            # squashes the raw score into (-1, +1) with tanh


def evaluate(game, state, player):
    # How good `state` looks for `player`, from -1 (lost) to +1 (won).
    #   1. A finished game gives its exact utility.
    #   2. If the player to move can win right now, the position is almost won
    #      for them (they just play that column).
    #   3. Otherwise count the open windows of each player (more pieces in an
    #      open window = closer to four in a row) and the centre pieces.
    if game.is_terminal(state):
        return float(game.utility(state, player))

    mover = state.to_move
    if game.winning_moves(state, mover):
        return 0.9 if mover == player else -0.9

    opponent = other(player)
    board = state.board
    score = 0
    for a, b, c, d in WINDOWS:
        cells = board[a] + board[b] + board[c] + board[d]   # e.g. "XX.O"
        mine, theirs = cells.count(player), cells.count(opponent)
        if mine and not theirs:
            score += WINDOW_POINTS[mine]
        elif theirs and not mine:
            score -= WINDOW_POINTS[theirs]

    centre = [board[cell(r, COLS // 2)] for r in range(ROWS)]
    score += CENTRE_POINTS * (centre.count(player) - centre.count(opponent))

    return 0.8 * math.tanh(score / SCALE)   # stays below the "can win now" value
