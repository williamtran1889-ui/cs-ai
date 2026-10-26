# Wheel of Fortune — the wheel

WT's Sprint 1 stories:

| # | Story | Short title | Complexity |
|---|-------|-------------|-----------|
| 3 | As the host, I want a wheel to be created for the current round so that each round has different arrangement of values. | create wheel | 5 |
| 5 | As a player, I want to be able to spin the wheel and see the result so that I know the dollar value for my current guess. | spin wheel | 10 |

Python 3.8+, standard library only.

## Try it

```bash
python3 -m wheel_of_fortune            # Enter = spin, n = next round, q = quit
python3 -m wheel_of_fortune --seed 7   # same wheel and spins every time
python3 -m unittest discover -v        # run the tests from the repo root
```

## Using it from other stories

```python
from wheel_of_fortune import create_wheel

wheel = create_wheel(round_number)  # new shuffled wheel for this round
result = wheel.spin()

result.wedge.label   # "$650", "BANKRUPT" or "LOSE A TURN"
result.is_cash       # False for BANKRUPT / LOSE A TURN
result.value         # dollars per consonant; 0 on a penalty wedge
result.message()     # text to show the player
```

- **Consonant guess (#7):** winnings are `result.value * letters_found` when `result.is_cash`.
- **Lose turn / bankrupt (#10):** check `result.wedge.kind` against `WedgeType.BANKRUPT` and `WedgeType.LOSE_A_TURN`.
- **Visualize spin (#6):** each result carries `start_angle`, `rotation` and `end_angle` (degrees), so the animation can turn the wheel from where it was to where it stopped. Wedge `i` covers `i * wheel.degrees_per_wedge` up to the next wedge, and the pointer is at 0°.

## How the wheel is built

- 24 wedges every round: one top-dollar wedge, 2 BANKRUPT, 1 LOSE A TURN, and the rest regular cash values.
- Values climb by round: top dollar is $2,500 in round 1, $3,500 in round 2 and $5,000 from round 3 on (see `ROUND_CONFIGS` in `wheel.py`).
- The wedges are shuffled for each round, and penalty wedges are never placed next to each other.
- Each spin turns the wheel 2–4 full rotations from where it last stopped.
