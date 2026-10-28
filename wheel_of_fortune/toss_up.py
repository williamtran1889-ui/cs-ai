"""Toss-up puzzle in the terminal: python -m wheel_of_fortune.toss_up [--seed N]

Story #14: the toss-up phrase is shown letter by letter until a player buzzes
in (Ctrl+C) with an answer. Story #4's turn order is shown first.
"""

from __future__ import annotations

import argparse
import random
import time
from typing import Callable, List, Sequence

from .players import play_order, prompt_players
from .puzzles import load_puzzle


def mask(phrase: str, shown: Sequence[int]) -> str:
    """The phrase as blanks, with the letters at the ``shown`` positions filled in."""
    display = ""
    for i, letter in enumerate(phrase):
        if letter == " ":
            display += "  "
        elif i in shown:
            display += letter + " "
        else:
            display += "_ "  # the space keeps the blanks from running together
    return display


def reveal_order(phrase: str, rng: random.Random | None = None) -> List[int]:
    """Positions of the letters in the order they are revealed (random, spaces skipped)."""
    positions = [i for i, letter in enumerate(phrase) if letter != " "]
    (rng or random).shuffle(positions)
    return positions


def is_correct(phrase: str, answer: str) -> bool:
    return answer.strip().upper() == phrase


def play(
    phrase: str,
    rng: random.Random | None = None,
    ask: Callable[[str], str] = input,
    show: Callable[..., None] = print,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    """Run one toss-up; returns "correct", "wrong" or "nobody" (letters ran out)."""
    show(mask(phrase, []))
    show("Press Ctrl+C to buzz in")

    shown: List[int] = []
    try:
        for position in reveal_order(phrase, rng):
            shown.append(position)
            show(mask(phrase, shown))
            sleep(1)  # one letter per second
        show("nobody got the answer, phrase was:", phrase)
        return "nobody"
    except KeyboardInterrupt:
        show("\nBuzz!")
        if is_correct(phrase, ask("Your Answer: ")):
            show("Bingo! Correct")
            return "correct"
        show("Wrong! The phrase was:", phrase)
        return "wrong"


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Play a Wheel of Fortune toss-up in the terminal.")
    parser.add_argument("--seed", type=int, help="seed the player order and puzzle for repeatable games")
    args = parser.parse_args(argv)
    rng = random.Random(args.seed)

    try:
        players = prompt_players()
    except (EOFError, KeyboardInterrupt):
        print()
        return

    print("Determining player playing order")
    print("Playing order:", ", ".join(play_order(players, rng)))
    play(load_puzzle(rng)["answer"], rng)


if __name__ == "__main__":
    main()
