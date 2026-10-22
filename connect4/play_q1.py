# ------------------------------------------------------------------------
# play_q1.py
# Question 1 - Plays full games of Connect Four between two players.
# Used for the live demo and for the tournaments in experiments_q1.py.
#
# Run from the project root:
#   python -m connect4.play_q1                          (MCTS as X vs Random as O)
#   python -m connect4.play_q1 --o mcts --o-iterations 200
#   python -m connect4.play_q1 --x human                (you play X against MCTS)
# ------------------------------------------------------------------------

import argparse

from connect4.game_q1 import X, O, ConnectFour
from connect4.mcts_q1 import MCTSConfig, MCTSPlayer, RandomPlayer


def human_player(game, state):
    # Asks the user for a column until a legal one is typed.
    legal = game.actions(state)
    while True:
        try:
            text = input(f"{state.to_move}, choose a column {legal}: ")
        except EOFError:                # input closed (Ctrl+D / Ctrl+Z): stop the game
            raise SystemExit("\nGame stopped.")
        if text.strip().isdigit() and int(text) in legal:
            return int(text)
        print("Not a legal move, try again.")


def play_game(game, player_x, player_o, verbose=False):
    # Plays one game and returns the winner ("X", "O") or None for a draw.
    players = {X: player_x, O: player_o}
    state = game.initial
    while not game.is_terminal(state):
        move = players[state.to_move](game, state)
        state = game.result(state, move)
        if verbose:
            print(f"\n{just_moved(state)} plays column {move}")
            print(game.display(state))
    return state.winner


def just_moved(state):
    # The player who made the last move (the one NOT to move now).
    return O if state.to_move == X else X


def make_player(kind, iterations, seed):
    if kind == "mcts":
        return MCTSPlayer(MCTSConfig(iterations=iterations, seed=seed))
    if kind == "random":
        return RandomPlayer(seed)
    return human_player


def main():
    parser = argparse.ArgumentParser(description="Play Connect Four")
    parser.add_argument("--x", choices=["mcts", "random", "human"], default="mcts")
    parser.add_argument("--o", choices=["mcts", "random", "human"], default="random")
    parser.add_argument("--x-iterations", type=int, default=500)
    parser.add_argument("--o-iterations", type=int, default=500)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    game = ConnectFour()
    player_x = make_player(args.x, args.x_iterations, args.seed)
    player_o = make_player(args.o, args.o_iterations, None if args.seed is None else args.seed + 1)

    print(game.display(game.initial))
    winner = play_game(game, player_x, player_o, verbose=True)
    print("\nDraw!" if winner is None else f"\n{winner} wins!")


if __name__ == "__main__":
    main()
