# Wheel of Fortune Project

A Wheel of Fortune game built by the Athletes group. Sprint 1 pieces from three people now share one package and one set of puzzle data.

## How it fits together

```
wheel_of_fortune/            shared game code (Python 3.8+, standard library only)
  wheel.py                   create + spin the wheel                        (stories #3, #5)
  players.py                 2-5 players, random order, turn rotation       (story #4)
  toss_up.py                 letter-by-letter toss-up in the terminal       (story #14)
  puzzles.py                 loads + validates the puzzle data, board layout
  data/                      categories.json, phrases.json, hints.json - the only copy
stories_rz/                  Flask web game: puzzle board, guess, vowels, solve, rounds
tests/                       unittest suite for all of the above
```

The web game (`stories_rz/app.py`) is where the pieces meet:

- **puzzles.py** picks the puzzle and lays it out on the 52-tile board.
- **players.py** orders the players and passes the turn.
- **wheel.py** builds one wheel per round (values climb each round) and every spin uses that wheel. A cash spin sets what each consonant is worth; BANKRUPT and LOSE A TURN pass the turn.
- **toss_up.py** reads the same phrases through `puzzles.py`.

## Run it

```bash
# Web game (needs Flask)
pip install -r stories_rz/requirements.txt
python stories_rz/app.py                # then open http://127.0.0.1:5000

# Terminal pieces (no extra installs)
python -m wheel_of_fortune              # try the wheel: Enter = spin, n = next round, q = quit
python -m wheel_of_fortune.toss_up      # players + turn order, then a toss-up (Ctrl+C to buzz in)
```

## Test it

```bash
python -m unittest discover -v          # from the repo root
```

The web tests need Flask and are skipped when it is not installed.

## Not built yet

- The toss-up only runs in the terminal; the web game does not offer it yet.
- Spin animation (story #6): spin results already carry `start_angle` / `end_angle` for it.
- Scoring beyond a running total: money carries over between rounds, with no round banking or end of game.
- The web game keeps its state in the browser session, so it is one game per browser.
