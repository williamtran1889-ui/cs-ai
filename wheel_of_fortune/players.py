"""Players and turn order.

Story #4: players are prompted for, put in a random order, and take turns in
that order so the game proceeds in an orderly and fair manner.
"""

from __future__ import annotations

import random
from typing import Callable, List, Sequence

MIN_PLAYERS = 2
MAX_PLAYERS = 5


def clean_names(names: Sequence[str]) -> List[str]:
    """Strip names and drop blank ones; ValueError unless 2 to 5 players remain."""
    cleaned = [name.strip() for name in names if name and name.strip()]
    if not MIN_PLAYERS <= len(cleaned) <= MAX_PLAYERS:
        raise ValueError(f"Enter between {MIN_PLAYERS} and {MAX_PLAYERS} player names.")
    return cleaned


def play_order(names: Sequence[str], rng: random.Random | None = None) -> List[str]:
    """The players in a random order; the first one takes the first turn."""
    order = list(names)
    (rng or random).shuffle(order)
    return order


def next_turn(turn: int, player_count: int) -> int:
    """Index of the player after ``turn``, wrapping back to the first player."""
    return (turn + 1) % player_count


def prompt_players(ask: Callable[[str], str] = input, show: Callable[..., None] = print) -> List[str]:
    """Ask in the terminal how many players there are and what they are called."""
    count = 0
    while not MIN_PLAYERS <= count <= MAX_PLAYERS:
        try:
            count = int(ask(f"How many players will be playing? (between {MIN_PLAYERS} and {MAX_PLAYERS}): "))
        except ValueError:
            count = 0
        if not MIN_PLAYERS <= count <= MAX_PLAYERS:
            show(f"Please enter a number from {MIN_PLAYERS} to {MAX_PLAYERS}.")

    names = []
    for number in range(1, count + 1):
        names.append(ask(f"Enter name for player {number}: ").strip() or f"Player {number}")
    return names
