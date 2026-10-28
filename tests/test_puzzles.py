import random
import unittest
from unittest import mock

from wheel_of_fortune.puzzles import BOARD_ROWS, arrange_words, fits_board, load_puzzle, load_puzzles


def words_per_row(answer):
    return [" ".join("".join(word) for word in row) for row in arrange_words(answer, BOARD_ROWS)]


class PuzzleDataTest(unittest.TestCase):
    """The category, phrase and hint files line up and every phrase can be shown on the board."""

    def test_data_files_load_and_validate(self):
        puzzles = load_puzzles()
        self.assertGreater(len(puzzles), 0)
        for puzzle in puzzles:
            self.assertEqual(set(puzzle), {"category", "answer", "hint"})
            self.assertTrue(puzzle["hint"].strip(), f"{puzzle['answer']} has no hint")

    def test_every_phrase_fits_the_board_without_dropping_words(self):
        for puzzle in load_puzzles():
            placed = [word for row in arrange_words(puzzle["answer"], BOARD_ROWS) for word in row]
            self.assertEqual(["".join(word) for word in placed], puzzle["answer"].split(), puzzle["answer"])

    def test_phrases_from_the_original_app_data_are_kept(self):
        answers = {p["answer"] for p in load_puzzles()}
        self.assertIn("FISH AND CHIPS", answers)
        self.assertIn("TEAMWORK MAKES THE DREAM WORK", answers)

    def test_words_wrap_onto_rows_without_splitting(self):
        self.assertEqual(
            words_per_row("ACTIONS SPEAK LOUDER THAN WORDS"),
            ["ACTIONS", "SPEAK LOUDER", "THAN WORDS", ""],
        )

    def test_a_phrase_too_long_for_the_board_does_not_fit(self):
        self.assertFalse(fits_board("A" * 15))  # no row is wider than 14
        self.assertFalse(fits_board(" ".join(["WORDS"] * 10)))  # more than four rows
        self.assertTrue(fits_board("HOME ALONE"))

    def test_load_puzzle_picks_from_the_data_and_honours_the_seed(self):
        self.assertEqual(load_puzzle(random.Random(4)), load_puzzle(random.Random(4)))
        self.assertIn(load_puzzle(random.Random(4)), load_puzzles())


class BadPuzzleDataTest(unittest.TestCase):
    def load_with(self, categories, phrases, hints):
        files = {"categories.json": {"categories": categories}, "phrases.json": {"phrases": phrases}, "hints.json": {"hints": hints}}
        with mock.patch("wheel_of_fortune.puzzles.load_json", side_effect=files.__getitem__):
            return load_puzzles()

    def test_valid_data_is_accepted(self):
        puzzles = self.load_with(["FOOD"], [["ice cream"]], [["Cold"]])
        self.assertEqual(puzzles, [{"category": "FOOD", "answer": "ICE CREAM", "hint": "Cold"}])

    def test_category_counts_must_match(self):
        with self.assertRaisesRegex(ValueError, "counts must match"):
            self.load_with(["A", "B"], [["ONE"]], [["hint"]])

    def test_every_phrase_needs_a_hint(self):
        with self.assertRaisesRegex(ValueError, "matching hint"):
            self.load_with(["A"], [["ONE", "TWO"]], [["only one hint"]])

    def test_phrases_may_only_be_letters_and_spaces(self):
        for bad in ("ROUTE 66", "DON'T STOP", "CAFÉ"):
            with self.assertRaisesRegex(ValueError, "letters"):
                self.load_with(["A"], [[bad]], [["hint"]])

    def test_phrases_must_fit_the_board(self):
        with self.assertRaisesRegex(ValueError, "board"):
            self.load_with(["A"], [["SUPERCALIFRAGILISTIC"]], [["hint"]])


if __name__ == "__main__":
    unittest.main()
