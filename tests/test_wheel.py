import contextlib
import io
import json
import random
import unittest
from unittest import mock

from wheel_of_fortune import WedgeType, Wheel, Wedge, create_wheel
from wheel_of_fortune.__main__ import main, pointer_view
from wheel_of_fortune.wheel import MAX_SPIN_DEGREES, MIN_SPIN_DEGREES, WEDGE_COUNT, round_config


def count(wheel, kind):
    return sum(1 for w in wheel.wedges if w.kind is kind)


class CreateWheelTest(unittest.TestCase):
    """Story #3: a wheel is created for each round with its own arrangement."""

    def test_every_round_has_a_full_wheel(self):
        for round_number in range(1, 6):
            self.assertEqual(len(create_wheel(round_number, random.Random(round_number)).wedges), WEDGE_COUNT)

    def test_round_one_layout(self):
        wheel = create_wheel(1, random.Random(1))
        self.assertEqual(wheel.round_number, 1)
        self.assertEqual(count(wheel, WedgeType.BANKRUPT), 2)
        self.assertEqual(count(wheel, WedgeType.LOSE_A_TURN), 1)
        self.assertEqual(count(wheel, WedgeType.CASH), WEDGE_COUNT - 3)
        self.assertEqual(max(w.value for w in wheel.wedges), 2500)

    def test_values_climb_each_round(self):
        top = [max(w.value for w in create_wheel(n, random.Random(n)).wedges) for n in (1, 2, 3)]
        self.assertEqual(top, [2500, 3500, 5000])

    def test_rounds_after_the_last_config_reuse_it(self):
        self.assertIs(round_config(7), round_config(3))

    def test_invalid_round_is_rejected(self):
        for bad in (0, -1):
            with self.assertRaises(ValueError):
                create_wheel(bad)

    def test_each_round_gets_a_different_arrangement(self):
        rng = random.Random(42)
        layouts = [create_wheel(4, rng).wedges for _ in range(5)]  # same values, so only the order differs
        self.assertEqual(len(set(layouts)), len(layouts))

    def test_same_seed_gives_same_wheel(self):
        self.assertEqual(create_wheel(2, random.Random(7)).wedges, create_wheel(2, random.Random(7)).wedges)

    def test_penalty_wedges_never_touch(self):
        for seed in range(500):
            wedges = create_wheel(1 + seed % 3, random.Random(seed)).wedges
            for i in range(len(wedges)):
                # i - 1 wraps to the last wedge, so this also checks across the seam.
                self.assertFalse(
                    not wedges[i].is_cash and not wedges[i - 1].is_cash,
                    f"seed {seed}: penalties next to each other at {i - 1} and {i}",
                )

    def test_wheel_prints_every_wedge(self):
        wheel = create_wheel(1, random.Random(3))
        text = str(wheel)
        self.assertTrue(text.startswith("Round 1 wheel:"))
        self.assertIn("$2,500", text)
        self.assertIn("BANKRUPT", text)
        self.assertIn("LOSE A TURN", text)


class SpinWheelTest(unittest.TestCase):
    """Story #5: a player spins and sees the dollar value for their guess."""

    def test_spin_lands_on_the_wedge_under_the_pointer(self):
        wheel = create_wheel(1, random.Random(5))
        for _ in range(100):
            result = wheel.spin()
            self.assertEqual(result.index, wheel.index_at(result.end_angle))
            self.assertIs(result.wedge, wheel.wedges[result.index])
            self.assertAlmostEqual(result.end_angle, wheel.angle)

    def test_spin_turns_at_least_two_full_rotations(self):
        wheel = create_wheel(1, random.Random(6))
        for _ in range(100):
            self.assertTrue(MIN_SPIN_DEGREES <= wheel.spin().rotation <= MAX_SPIN_DEGREES)

    def test_next_spin_starts_where_the_last_one_stopped(self):
        wheel = create_wheel(1, random.Random(8))
        first = wheel.spin()
        second = wheel.spin()
        self.assertAlmostEqual(second.start_angle, first.end_angle)

    def test_every_wedge_can_be_landed_on(self):
        wheel = create_wheel(1, random.Random(9))
        landed = {wheel.spin().index for _ in range(2000)}
        self.assertEqual(landed, set(range(WEDGE_COUNT)))

    def test_cash_result_reports_its_dollar_value(self):
        wheel = Wheel([Wedge(WedgeType.CASH, 650)], rng=random.Random(1))
        result = wheel.spin()
        self.assertTrue(result.is_cash)
        self.assertEqual(result.value, 650)
        self.assertIn("$650", result.message())

    def test_penalty_results_have_no_value(self):
        for kind, text in ((WedgeType.BANKRUPT, "BANKRUPT"), (WedgeType.LOSE_A_TURN, "LOSE A TURN")):
            result = Wheel([Wedge(kind)], rng=random.Random(1)).spin()
            self.assertFalse(result.is_cash)
            self.assertEqual(result.value, 0)
            self.assertIn(text, result.message())

    def test_empty_wheel_is_rejected(self):
        with self.assertRaises(ValueError):
            Wheel([])


class KeepWheelBetweenRequestsTest(unittest.TestCase):
    """The web game keeps one wheel per round, so a wheel must survive being saved and reloaded."""

    def test_round_trip_keeps_wedges_round_and_angle(self):
        wheel = create_wheel(2, random.Random(11))
        wheel.spin()
        copy = Wheel.from_dict(wheel.to_dict())
        self.assertEqual(copy.wedges, wheel.wedges)
        self.assertEqual(copy.round_number, 2)
        self.assertEqual(copy.angle, wheel.angle)

    def test_saved_wheel_is_plain_json_data(self):
        saved = create_wheel(1, random.Random(1)).to_dict()
        self.assertEqual(json.loads(json.dumps(saved)), saved)

    def test_a_reloaded_wheel_spins_on_from_where_it_stopped(self):
        wheel = create_wheel(1, random.Random(12))
        first = wheel.spin()
        second = Wheel.from_dict(wheel.to_dict(), random.Random(13)).spin()
        self.assertAlmostEqual(second.start_angle, first.end_angle)


class CommandLineTest(unittest.TestCase):
    def test_pointer_marks_the_landed_wedge(self):
        wheel = Wheel([Wedge(WedgeType.CASH, v) for v in (100, 200, 300, 400, 500)])
        top, pointer = pointer_view(wheel, 0).split("\n")
        self.assertEqual(top, "$400 | $500 | [$100] | $200 | $300")
        self.assertEqual(pointer.strip(), "^")
        self.assertTrue(top.index("[") < len(pointer) - 1 < top.index("]"))  # pointer sits under "[$100]"

    def test_spin_next_round_and_quit(self):
        out = io.StringIO()
        with mock.patch("builtins.input", side_effect=["", "n", "", "q"]), contextlib.redirect_stdout(out):
            main(["--seed", "1"])
        text = out.getvalue()
        self.assertIn("Round 1 wheel:", text)
        self.assertIn("Round 2 wheel:", text)
        self.assertEqual(text.count("^"), 2)


if __name__ == "__main__":
    unittest.main()
