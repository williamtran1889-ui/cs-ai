"""The game wheel: building a fresh wheel for each round and spinning it.

Sprint 1 stories owned by WT:
  #3 Create wheel - each round gets its own arrangement of values.
  #5 Spin wheel   - a player spins and sees the dollar value for their guess.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

WEDGE_COUNT = 24

# Every spin turns the wheel 2 to 4 full rotations, so it never just nudges
# over to the neighbouring wedge.
MIN_SPIN_DEGREES = 720.0
MAX_SPIN_DEGREES = 1440.0


class WedgeType(Enum):
    CASH = "cash"
    BANKRUPT = "bankrupt"
    LOSE_A_TURN = "lose_a_turn"


@dataclass(frozen=True)
class Wedge:
    kind: WedgeType
    value: int = 0  # dollar value; 0 for BANKRUPT and LOSE A TURN

    @property
    def is_cash(self) -> bool:
        return self.kind is WedgeType.CASH

    @property
    def label(self) -> str:
        if self.kind is WedgeType.CASH:
            return f"${self.value:,}"
        if self.kind is WedgeType.BANKRUPT:
            return "BANKRUPT"
        return "LOSE A TURN"

    def __str__(self) -> str:
        return self.label


@dataclass(frozen=True)
class RoundConfig:
    cash_values: tuple[int, ...]  # repeated in order to fill the regular cash wedges
    top_dollar: int
    bankrupts: int = 2
    lose_a_turns: int = 1


# Values climb each round like on the TV show. Rounds past the last entry reuse it.
ROUND_CONFIGS = (
    RoundConfig(cash_values=(500, 550, 600, 650, 700, 800, 900), top_dollar=2500),
    RoundConfig(cash_values=(500, 600, 700, 800, 900, 1000), top_dollar=3500),
    RoundConfig(cash_values=(600, 700, 800, 900, 1000, 1500), top_dollar=5000),
)


def round_config(round_number: int) -> RoundConfig:
    if round_number < 1:
        raise ValueError(f"round_number must be 1 or higher, got {round_number}")
    return ROUND_CONFIGS[min(round_number, len(ROUND_CONFIGS)) - 1]


@dataclass(frozen=True)
class SpinResult:
    wedge: Wedge
    index: int  # position of the wedge on the wheel
    start_angle: float  # where the wheel sat before the spin, for animating it later (story #6)
    rotation: float  # how many degrees the wheel turned

    @property
    def end_angle(self) -> float:
        return (self.start_angle + self.rotation) % 360

    @property
    def value(self) -> int:
        """Dollar value of the spin; 0 when the player lands on a penalty wedge."""
        return self.wedge.value

    @property
    def is_cash(self) -> bool:
        return self.wedge.is_cash

    def message(self) -> str:
        if self.wedge.kind is WedgeType.CASH:
            return f"You landed on {self.wedge.label}! Each correct consonant is worth {self.wedge.label}."
        if self.wedge.kind is WedgeType.BANKRUPT:
            return "BANKRUPT! You lose your money for this round and your turn."
        return "LOSE A TURN. Play passes to the next player."


class Wheel:
    """A wheel for one round. The pointer is fixed at 0 degrees; spinning turns
    the wheel, and the wedge covering ``angle`` is the one under the pointer."""

    def __init__(self, wedges: Sequence[Wedge], round_number: int = 1, rng: random.Random | None = None):
        if not wedges:
            raise ValueError("a wheel needs at least one wedge")
        self.wedges = tuple(wedges)
        self.round_number = round_number
        self.angle = 0.0
        self._rng = rng or random.Random()

    @property
    def degrees_per_wedge(self) -> float:
        return 360 / len(self.wedges)

    def index_at(self, angle: float) -> int:
        return int((angle % 360) // self.degrees_per_wedge) % len(self.wedges)

    def spin(self) -> SpinResult:
        start = self.angle
        rotation = self._rng.uniform(MIN_SPIN_DEGREES, MAX_SPIN_DEGREES)
        self.angle = (start + rotation) % 360
        index = self.index_at(self.angle)
        return SpinResult(self.wedges[index], index, start, rotation)

    def to_dict(self) -> dict:
        """Plain data for keeping the wheel between requests (e.g. in a web session)."""
        return {
            "round_number": self.round_number,
            "angle": self.angle,
            "wedges": [[w.kind.value, w.value] for w in self.wedges],
        }

    @classmethod
    def from_dict(cls, data: dict, rng: random.Random | None = None) -> Wheel:
        """Rebuild a wheel from ``to_dict``: same wedges, round and resting angle."""
        wedges = [Wedge(WedgeType(kind), value) for kind, value in data["wedges"]]
        wheel = cls(wedges, data["round_number"], rng)
        wheel.angle = data["angle"]
        return wheel

    def __str__(self) -> str:
        labels = [w.label for w in self.wedges]
        rows = [" | ".join(f"{label:>11}" for label in labels[i:i + 6]) for i in range(0, len(labels), 6)]
        return f"Round {self.round_number} wheel:\n" + "\n".join(rows)


def create_wheel(round_number: int, rng: random.Random | None = None) -> Wheel:
    """Build a shuffled wheel for ``round_number``.

    The round decides which values are on the wheel; the shuffle gives each
    round its own arrangement. Penalty wedges are never placed next to each
    other (including across the wrap-around), like on the show.
    """
    config = round_config(round_number)
    rng = rng or random.Random()

    penalties = [Wedge(WedgeType.BANKRUPT)] * config.bankrupts + [Wedge(WedgeType.LOSE_A_TURN)] * config.lose_a_turns
    cash_slots = WEDGE_COUNT - len(penalties) - 1
    cash = [Wedge(WedgeType.CASH, config.top_dollar)]
    cash += [Wedge(WedgeType.CASH, config.cash_values[i % len(config.cash_values)]) for i in range(cash_slots)]
    rng.shuffle(cash)
    rng.shuffle(penalties)

    # Drop each penalty into a different gap after a cash wedge so no two touch.
    gaps = set(rng.sample(range(len(cash)), len(penalties)))
    remaining_penalties = iter(penalties)
    wedges = []
    for i, wedge in enumerate(cash):
        wedges.append(wedge)
        if i in gaps:
            wedges.append(next(remaining_penalties))

    return Wheel(wedges, round_number, rng)
