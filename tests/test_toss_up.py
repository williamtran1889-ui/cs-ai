import random
import unittest
from unittest import mock

from wheel_of_fortune import toss_up
from wheel_of_fortune.puzzles import load_puzzles


class TossUpDisplayTest(unittest.TestCase):
    """Story #14: the phrase appears letter by letter."""

    def test_mask_shows_blanks_for_letters_and_gaps_for_spaces(self):
        self.assertEqual(toss_up.mask("A B", []), "_   _ ")
        self.assertEqual(toss_up.mask("A B", [0]), "A   _ ")
        self.assertEqual(toss_up.mask("A B", [0, 2]), "A   B ")

    def test_reveal_order_covers_every_letter_once_and_skips_spaces(self):
        phrase = "BREAK THE ICE"
        order = toss_up.reveal_order(phrase, random.Random(2))
        self.assertCountEqual(order, [i for i, c in enumerate(phrase) if c != " "])

    def test_answers_ignore_case_and_surrounding_spaces(self):
        self.assertTrue(toss_up.is_correct("HOME ALONE", "  home alone "))
        self.assertFalse(toss_up.is_correct("HOME ALONE", "home alon"))


class TossUpPlayTest(unittest.TestCase):
    def play(self, answer=None, buzz_after=None):
        """Run a toss-up on "HI" (two letters); optionally buzz in after ``buzz_after`` letters."""
        shown, sleeps = [], []

        def sleep(seconds):
            sleeps.append(seconds)
            if len(sleeps) == buzz_after:
                raise KeyboardInterrupt

        result = toss_up.play(
            "HI", random.Random(1), ask=lambda prompt: answer, show=lambda *args: shown.append(" ".join(args)), sleep=sleep
        )
        return result, shown, sleeps

    def test_letters_run_out_when_nobody_buzzes(self):
        result, shown, sleeps = self.play()
        self.assertEqual(result, "nobody")
        self.assertEqual(sleeps, [1, 1])  # one letter per second
        self.assertIn("nobody got the answer, phrase was: HI", shown)

    def test_buzzing_in_with_the_right_answer(self):
        result, shown, sleeps = self.play(answer="hi", buzz_after=1)
        self.assertEqual(result, "correct")
        self.assertEqual(len(sleeps), 1)  # stopped revealing after the buzz
        self.assertIn("Bingo! Correct", shown)

    def test_buzzing_in_with_the_wrong_answer(self):
        result, shown, _ = self.play(answer="oh", buzz_after=1)
        self.assertEqual(result, "wrong")
        self.assertIn("Wrong! The phrase was: HI", shown)


class TossUpMainTest(unittest.TestCase):
    def test_main_orders_the_players_and_plays_a_phrase_from_the_shared_data(self):
        with mock.patch.object(toss_up, "prompt_players", return_value=["Ada", "Grace"]), mock.patch.object(
            toss_up, "play"
        ) as play, mock.patch("builtins.print") as printed:
            toss_up.main(["--seed", "3"])

        phrase = play.call_args.args[0]
        self.assertIn(phrase, [p["answer"] for p in load_puzzles()])
        order_line = next(c.args for c in printed.call_args_list if c.args and c.args[0] == "Playing order:")
        self.assertCountEqual(order_line[1].split(", "), ["Ada", "Grace"])


if __name__ == "__main__":
    unittest.main()
