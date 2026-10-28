# Wheel of Fortune

## Files
- `app.py`: Flask routes, guessing, buying vowels, solving, and scoring. It uses the shared `wheel_of_fortune` package one folder up for the wheel, the players and the puzzle data.
- `templates/index.html`: game board and controls.
- `static/style.css`: styling.
- `requirements.txt`: dependency list.

The puzzle data (`categories.json`, `phrases.json`, `hints.json`) lives in `../wheel_of_fortune/data/` so the web game and the toss-up share one copy. The category at index `i` in `categories.json` matches the phrase and hint lists at index `i` in the other files. Within each category, each phrase must match the hint at the same index. Phrases may only use the letters A-Z and spaces, and must fit on the 52-tile board.

## Run on Windows PowerShell
1. Open PowerShell in this folder.
2. Create a virtual environment if needed: `py -m venv .venv`
3. Activate it: `.\.venv\Scripts\Activate.ps1`
4. Install Flask: `python -m pip install -r requirements.txt`
5. Run: `python app.py`
6. Visit `http://127.0.0.1:5000`.

If `python` cannot be found, try `py app.py` or `.\.venv\Scripts\python.exe app.py`.

## Run on Linux or macOS
1. Open Terminal in this folder.
2. Create a virtual environment if needed: `python3 -m venv .venv`
3. Activate it: `source .venv/bin/activate`
4. Install Flask: `python -m pip install -r requirements.txt`
5. Run: `python app.py`
6. Visit `http://127.0.0.1:5000`.

Sessions are signed with a random key made each time the app starts, so a restart ends any game in progress. Set `WOF_SECRET_KEY` to keep games across restarts.

## Behavior
- Before START, all 52 tiles are green. No category, hint, guess controls, or counts appear below the board.
- START needs 2 to 5 player names. The players are put in a random order and the first player takes the first turn.
- START selects a random category, phrase, and matching hint, and builds the wheel for round 1.
- Phrase letters occupy white tiles; phrase spaces and unused tiles remain green. Tile sizes and spacing stay uniform.
- SPIN THE WHEEL turns the round's wheel. Its result decides what happens next:
  - A dollar value: the player must guess a consonant. Each correct occurrence earns that value, and the player keeps the turn. A consonant that is not in the phrase passes the turn.
  - BANKRUPT: the player's money goes to $0 and the turn passes.
  - LOSE A TURN: the turn passes.
- Buying a vowel costs $250. A vowel that is not in the phrase passes the turn.
- A wrong solution passes the turn. Solving the puzzle, or revealing its last letter, wins the round.
- NEXT ROUND gives a new puzzle and a new wheel (top dollar: $2,500, then $3,500, then $5,000 from round 3). The starting player rotates each round, and money carries over.
- Previously guessed letters are displayed and cannot be guessed twice.
