"""Try the wheel from a terminal: python -m wheel_of_fortune [--seed N]"""

import argparse
import random

from .wheel import Wheel, create_wheel


def pointer_view(wheel: Wheel, index: int, neighbours: int = 2) -> str:
    """Show the landed wedge with its neighbours and a pointer under it."""
    count = len(wheel.wedges)
    labels = [wheel.wedges[(index + offset) % count].label for offset in range(-neighbours, neighbours + 1)]
    labels[neighbours] = f"[{labels[neighbours]}]"
    left = len(" | ".join(labels[:neighbours])) + 3 if neighbours else 0
    pointer = " " * (left + len(labels[neighbours]) // 2) + "^"
    return " | ".join(labels) + "\n" + pointer


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Create and spin a Wheel of Fortune wheel.")
    parser.add_argument("--seed", type=int, help="seed the wheel for repeatable spins")
    args = parser.parse_args(argv)

    rng = random.Random(args.seed)
    wheel = create_wheel(1, rng)
    print(wheel)

    while True:
        try:
            choice = input("\n[Enter] spin, [n] next round, [q] quit: ").strip().lower()
        except EOFError:
            break
        if choice == "q":
            break
        if choice == "n":
            wheel = create_wheel(wheel.round_number + 1, rng)
            print(wheel)
            continue
        result = wheel.spin()
        print(pointer_view(wheel, result.index))
        print(result.message())


if __name__ == "__main__":
    main()
