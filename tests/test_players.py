import random
import unittest

from wheel_of_fortune.players import MAX_PLAYERS, MIN_PLAYERS, clean_names, next_turn, play_order, prompt_players


class PlayerSetupTest(unittest.TestCase):
    """Story #4: 2 to 5 players, put in a random order."""

    def test_names_are_stripped_and_blanks_dropped(self):
        self.assertEqual(clean_names([" Ada ", "", "  ", "Grace"]), ["Ada", "Grace"])

    def test_player_count_limits(self):
        self.assertEqual(len(clean_names(["a", "b"])), MIN_PLAYERS)
        self.assertEqual(len(clean_names(list("abcde"))), MAX_PLAYERS)
        for names in ([], ["a"], ["a", " "], list("abcdef")):
            with self.assertRaises(ValueError):
                clean_names(names)

    def test_play_order_is_a_shuffle_of_the_same_players(self):
        names = ["Ada", "Grace", "Linus", "Margaret"]
        order = play_order(names, random.Random(1))
        self.assertCountEqual(order, names)
        self.assertEqual(names, ["Ada", "Grace", "Linus", "Margaret"])  # input untouched

    def test_play_order_is_repeatable_with_a_seed_and_varies_without_one(self):
        names = ["Ada", "Grace", "Linus"]
        self.assertEqual(play_order(names, random.Random(5)), play_order(names, random.Random(5)))
        self.assertEqual({play_order(names, random.Random(seed))[0] for seed in range(50)}, set(names))


class TurnOrderTest(unittest.TestCase):
    def test_turns_go_round_in_order_and_wrap(self):
        turn, seen = 0, []
        for _ in range(7):
            seen.append(turn)
            turn = next_turn(turn, 3)
        self.assertEqual(seen, [0, 1, 2, 0, 1, 2, 0])

    def test_two_players_alternate(self):
        self.assertEqual([next_turn(0, 2), next_turn(1, 2)], [1, 0])


class PromptPlayersTest(unittest.TestCase):
    def run_prompt(self, answers):
        answers = iter(answers)
        shown = []
        names = prompt_players(ask=lambda prompt: next(answers), show=shown.append)
        return names, shown

    def test_asks_for_the_count_then_each_name(self):
        names, shown = self.run_prompt(["2", "Ada", "Grace"])
        self.assertEqual(names, ["Ada", "Grace"])
        self.assertEqual(shown, [])

    def test_bad_counts_are_asked_again(self):
        names, shown = self.run_prompt(["1", "six", "9", "3", "Ada", "Grace", "Linus"])
        self.assertEqual(names, ["Ada", "Grace", "Linus"])
        self.assertEqual(len(shown), 3)

    def test_blank_names_get_a_default(self):
        names, _ = self.run_prompt(["2", "Ada", " "])
        self.assertEqual(names, ["Ada", "Player 2"])


if __name__ == "__main__":
    unittest.main()
