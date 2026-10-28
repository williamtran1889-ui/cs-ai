"""Puzzle data shared by every part of the game (web board, toss-up, tests).

The three files in ``data/`` are parallel lists: category ``i`` in
``categories.json`` owns the phrase list ``i`` in ``phrases.json`` and the hint
list ``i`` in ``hints.json``, and phrase ``j`` of a category matches hint ``j``.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"

# Tiles per row on the puzzle board (52 in total).
BOARD_ROWS = [12, 14, 14, 12]


def load_json(filename: str):
    with (DATA_DIR / filename).open(encoding="utf-8") as f:
        return json.load(f)


def arrange_words(answer: str, board_rows=BOARD_ROWS):
    """Lay the words of ``answer`` out on the board without splitting a word.

    Returns one list of words (each a list of letters) per board row. Words that
    do not fit are left out, so use ``fits_board`` to check a phrase first.
    """
    rows = [[] for _ in board_rows]
    row_index = 0

    for word in answer.split():
        if row_index >= len(board_rows):
            break

        while (
            row_index < len(board_rows)
            and sum(len(w) for w in rows[row_index]) + len(rows[row_index]) + len(word) > board_rows[row_index]
        ):
            row_index += 1

        if row_index >= len(board_rows):
            break

        rows[row_index].append(list(word))

    return rows


def fits_board(answer: str, board_rows=BOARD_ROWS) -> bool:
    placed = sum(len(row) for row in arrange_words(answer, board_rows))
    return placed == len(answer.split())


def load_puzzles():
    """Every puzzle as ``{"category", "answer", "hint"}``, validated.

    Raises ValueError for the first problem found, so bad data fails the same
    way every time instead of only when that puzzle happens to be picked.
    """
    categories = load_json("categories.json")["categories"]
    phrases = load_json("phrases.json")["phrases"]
    hints = load_json("hints.json")["hints"]

    if not (len(categories) == len(phrases) == len(hints)):
        raise ValueError("JSON category counts must match.")

    puzzles = []
    for category, category_phrases, category_hints in zip(categories, phrases, hints):
        if len(category_phrases) != len(category_hints) or not category_phrases:
            raise ValueError(f"Each phrase must have a matching hint (category {category!r}).")

        for phrase, hint in zip(category_phrases, category_hints):
            answer = phrase.strip().upper()
            if not answer.replace(" ", "").isalpha() or not answer.isascii():
                raise ValueError(f"Phrase {answer!r} may only contain the letters A-Z and spaces.")
            if not fits_board(answer):
                raise ValueError(f"Phrase {answer!r} must fit on the {sum(BOARD_ROWS)}-tile board.")
            puzzles.append({"category": category, "answer": answer, "hint": hint})

    return puzzles


def load_puzzle(rng: random.Random | None = None):
    """Pick one random puzzle: ``{"category", "answer", "hint"}``."""
    return (rng or random).choice(load_puzzles())
