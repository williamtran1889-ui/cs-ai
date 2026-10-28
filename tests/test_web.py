"""The Flask game: puzzle board + wheel + players working together.

Needs Flask (pip install -r stories_rz/requirements.txt); skipped without it.
"""

import html
import importlib.util
import re
import subprocess
import sys
import unittest
from pathlib import Path

HAS_FLASK = importlib.util.find_spec("flask") is not None
STORIES_RZ = Path(__file__).resolve().parent.parent / "stories_rz"

NAMES = ["Ada", "Grace", "Linus"]
ANSWER = "HOLLOW LOG"  # three Ls, and an easy G to finish on


def revealed_letters(body):
    """The letters showing on the board, in tile order (tiles still hidden are skipped)."""
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    return [letter for letter in re.findall(r'letter-tile">\s*([A-Z]?)\s*</div>', body) if letter]


def one_wedge_wheel(kind, value=0):
    """A wheel that can only land on one wedge, so a spin has a known result."""
    return {"round_number": 1, "angle": 0.0, "wedges": [[kind, value]]}


class AppStartsFromItsOwnFolderTest(unittest.TestCase):
    @unittest.skipUnless(HAS_FLASK, "Flask is not installed")
    def test_app_imports_when_run_from_stories_rz(self):
        """The folder README says `python app.py` from inside stories_rz/."""
        done = subprocess.run([sys.executable, "-c", "import app"], cwd=STORIES_RZ, capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)


@unittest.skipUnless(HAS_FLASK, "Flask is not installed (pip install -r stories_rz/requirements.txt)")
class WebGameTest(unittest.TestCase):
    def setUp(self):
        from stories_rz import app as web

        self.web = web
        web.app.config.update(TESTING=True)
        self.client = web.app.test_client()

    # -- helpers ---------------------------------------------------------
    def post(self, **data):
        return self.client.post("/", data=data, follow_redirects=True)

    @staticmethod
    def text(response):
        return html.unescape(response.get_data(as_text=True))

    def start(self, names=NAMES):
        return self.post(action="start", player=list(names))

    def state(self):
        with self.client.session_transaction() as saved:
            return dict(saved)

    def set_state(self, **changes):
        with self.client.session_transaction() as saved:
            saved.update(changes)

    def rig(self, wedge=("cash", 500), money=(0, 0, 0), turn=0, answer=ANSWER, **extra):
        """Start a real game, then fix the wheel, puzzle, money and turn so the outcome is known."""
        self.start()
        self.set_state(
            wheel=one_wedge_wheel(*wedge),
            game={"category": "TEST", "answer": answer, "hint": "a hint"},
            money=list(money),
            turn=turn,
            **extra,
        )

    def player(self, index):
        return self.state()["players"][index]

    # -- starting a game (story #4) ---------------------------------------
    def test_page_loads_before_a_game_starts(self):
        body = self.text(self.client.get("/"))
        self.assertIn("START", body)
        self.assertNotIn("SPIN THE WHEEL", body)
        self.assertEqual(body.count("green-tile"), 52)  # an empty board: every tile is green

    def test_start_needs_between_two_and_five_players(self):
        for names in (["Ada"], ["Ada", " "], list("abcdef")):
            body = self.text(self.start(names))
            self.assertIn("Enter between 2 and 5 player names.", body)
            self.assertNotIn("game", self.state())

    def test_start_puts_the_players_in_order_and_builds_the_round_one_wheel(self):
        body = self.text(self.start())
        state = self.state()
        self.assertCountEqual(state["players"], NAMES)
        self.assertEqual(state["money"], [0, 0, 0])
        self.assertEqual(state["turn"], 0)
        self.assertEqual(state["round_number"], 1)
        self.assertEqual(state["wheel"]["round_number"], 1)
        self.assertEqual(len(state["wheel"]["wedges"]), 24)
        for name in NAMES:
            self.assertIn(name, body)
        self.assertIn("SPIN THE WHEEL", body)
        self.assertIn(f"{state['players'][0]}, spin the wheel to begin!", body)

    def test_session_cookie_fits_in_a_browser_with_five_long_names(self):
        self.start(["N" * 20] * 5)
        self.set_state(game={"category": "SPORTS", "answer": "TEAMWORK MAKES THE DREAM WORK", "hint": "x" * 60})
        self.client.get("/")
        self.assertLess(len(self.client.get_cookie("session").value), 4000)

    # -- spinning (stories #3 and #5) -------------------------------------
    def test_every_spin_uses_the_wheel_built_for_the_round(self):
        self.start()
        wedges = self.state()["wheel"]["wedges"]
        angles = []
        for _ in range(5):
            self.set_state(can_guess=False)
            self.post(action="spin")
            saved = self.state()["wheel"]
            self.assertEqual(saved["wedges"], wedges)  # same arrangement all round
            angles.append(saved["angle"])
        self.assertGreater(len(set(angles)), 1)  # and it keeps turning from where it stopped

    def test_cash_spin_shows_the_dollar_value_and_waits_for_a_consonant(self):
        self.rig()
        body = self.text(self.post(action="spin"))
        state = self.state()
        self.assertEqual(state["current_spin"], 500)
        self.assertTrue(state["can_guess"])
        self.assertEqual(state["turn"], 0)
        self.assertIn("$500", body)

    def test_cannot_spin_again_before_guessing(self):
        self.rig()
        self.post(action="spin")
        body = self.text(self.post(action="spin"))
        self.assertIn("Guess a consonant before spinning again.", body)

    def test_bankrupt_zeroes_the_players_money_and_passes_the_turn(self):
        self.rig(wedge=("bankrupt", 0), money=(900, 300, 0))
        body = self.text(self.post(action="spin"))
        state = self.state()
        self.assertEqual(state["money"], [0, 300, 0])
        self.assertEqual(state["turn"], 1)
        self.assertIn("BANKRUPT", body)
        self.assertIn(f"{self.player(1)}, you're up.", body)

    def test_lose_a_turn_passes_the_turn_and_keeps_the_money(self):
        self.rig(wedge=("lose_a_turn", 0), money=(900, 0, 0))
        body = self.text(self.post(action="spin"))
        state = self.state()
        self.assertEqual(state["money"], [900, 0, 0])
        self.assertEqual(state["turn"], 1)
        self.assertIn("LOSE A TURN", body)

    def test_turns_wrap_back_to_the_first_player(self):
        self.rig(wedge=("lose_a_turn", 0), turn=2)
        self.post(action="spin")
        self.assertEqual(self.state()["turn"], 0)

    # -- guessing ---------------------------------------------------------
    def test_correct_consonant_pays_the_spin_value_per_letter_and_keeps_the_turn(self):
        self.rig()
        self.post(action="spin")
        body = self.text(self.post(action="guess", letter="l"))
        state = self.state()
        self.assertEqual(state["money"], [1500, 0, 0])  # three Ls at $500
        self.assertEqual(state["turn"], 0)
        self.assertFalse(state["can_guess"])
        self.assertIn("You earned $1,500.", body)

    def test_wrong_consonant_passes_the_turn(self):
        self.rig()
        self.post(action="spin")
        body = self.text(self.post(action="guess", letter="Z"))
        state = self.state()
        self.assertEqual(state["money"], [0, 0, 0])
        self.assertEqual(state["turn"], 1)
        self.assertIn("There is no Z in the phrase.", body)

    def test_guess_is_refused_without_a_spin_and_for_vowels_and_repeats(self):
        self.rig()
        self.assertIn("Please spin the wheel before guessing", self.text(self.post(action="guess", letter="L")))
        self.post(action="spin")
        self.assertIn("not a vowel", self.text(self.post(action="guess", letter="O")))
        self.assertIn("Enter one letter.", self.text(self.post(action="guess", letter="LL")))
        self.post(action="guess", letter="L")
        self.post(action="spin")
        self.assertIn("already guessed L", self.text(self.post(action="guess", letter="L")))
        self.assertEqual(self.state()["turn"], 0)  # none of those cost the player their turn

    def test_guessed_letters_are_revealed_on_the_board(self):
        self.rig()
        self.post(action="spin")
        body = self.text(self.post(action="guess", letter="G"))
        self.assertEqual(revealed_letters(body), ["G"])

    # -- vowels -----------------------------------------------------------
    def test_buying_a_vowel_costs_money_and_keeps_the_turn(self):
        self.rig(money=(400, 0, 0))
        self.post(action="buy_vowel", vowel="o")
        state = self.state()
        self.assertEqual(state["money"], [150, 0, 0])
        self.assertEqual(state["turn"], 0)
        self.assertIn("O", state["guessed_letters"])

    def test_a_vowel_not_in_the_puzzle_passes_the_turn(self):
        self.rig(money=(400, 0, 0))
        self.post(action="buy_vowel", vowel="U")
        state = self.state()
        self.assertEqual(state["money"], [150, 0, 0])
        self.assertEqual(state["turn"], 1)

    def test_vowel_needs_enough_money_and_a_real_vowel(self):
        self.rig(money=(100, 400, 0))
        self.assertIn("at least $250", self.text(self.post(action="buy_vowel", vowel="O")))
        self.set_state(money=[400, 0, 0])
        self.assertIn("valid vowel", self.text(self.post(action="buy_vowel", vowel="L")))
        self.assertEqual(self.state()["money"], [400, 0, 0])

    # -- finishing the round ----------------------------------------------
    def test_solving_wins_the_round_and_reveals_the_whole_puzzle(self):
        self.rig(money=(700, 0, 0))
        body = self.text(self.post(action="solve", solution="hollow log"))
        state = self.state()
        self.assertEqual(state["winner"], 0)
        self.assertIn("CORRECT!", body)
        self.assertIn(f"{self.player(0)} wins round 1!", body)
        self.assertIn("NEXT ROUND", body)
        self.assertNotIn("SPIN THE WHEEL", body)
        self.assertEqual(revealed_letters(body), list("HOLLOWLOG"))

    def test_a_wrong_solution_passes_the_turn(self):
        self.rig()
        body = self.text(self.post(action="solve", solution="something else"))
        self.assertEqual(self.state()["turn"], 1)
        self.assertIn("is incorrect!", body)
        self.assertIsNone(self.state()["winner"])

    def test_revealing_the_last_letter_wins_the_round(self):
        self.rig(guessed_letters=list("HOLW"), current_spin=500, can_guess=True)
        body = self.text(self.post(action="guess", letter="G"))
        self.assertEqual(self.state()["winner"], 0)
        self.assertIn("wins the round!", body)

    def test_nothing_can_be_played_once_the_round_is_won(self):
        self.rig(money=(700, 0, 0))
        self.post(action="solve", solution=ANSWER)
        before = self.state()
        self.post(action="spin")
        self.post(action="guess", letter="L")
        self.post(action="buy_vowel", vowel="O")
        self.post(action="solve", solution="nope")
        self.assertEqual(self.state(), before)

    def test_next_round_gets_a_new_puzzle_and_a_higher_value_wheel(self):
        self.rig(money=(700, 0, 0))
        self.post(action="solve", solution=ANSWER)
        self.post(action="next_round")
        state = self.state()
        self.assertEqual(state["round_number"], 2)
        self.assertEqual(state["wheel"]["round_number"], 2)
        self.assertEqual(max(value for _, value in state["wheel"]["wedges"]), 3500)  # top dollar climbs
        self.assertEqual(state["guessed_letters"], [])
        self.assertIsNone(state["winner"])
        self.assertEqual(state["turn"], 1)  # the starting player rotates
        self.assertEqual(state["money"], [700, 0, 0])

    def test_next_round_is_only_available_after_the_round_is_won(self):
        self.rig()
        self.post(action="next_round")
        self.assertEqual(self.state()["round_number"], 1)

    def test_restarting_with_new_players_resets_the_game(self):
        self.rig(money=(700, 0, 0))
        self.start(["Ann", "Bob"])
        state = self.state()
        self.assertCountEqual(state["players"], ["Ann", "Bob"])
        self.assertEqual(state["money"], [0, 0])
        self.assertEqual(state["round_number"], 1)

    def test_reset_clears_the_game(self):
        self.start()
        self.client.get("/reset")
        self.assertEqual(self.state(), {})


if __name__ == "__main__":
    unittest.main()
