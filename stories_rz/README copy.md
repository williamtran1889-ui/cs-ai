# Wheel of Fortune

## Files
- `app.py`: Flask routes, puzzle selection, guessing, and scoring.
- `categories.json`: category names.
- `phrases.json`: phrases grouped by category.
- `hints.json`: matching hints grouped by category and phrase.
- `templates/index.html`: game board and controls.
- `static/style.css`: styling.
- `requirements.txt`: dependency list.

The category at index `i` in `categories.json` matches the phrase and hint lists at index `i` in the other files. Within each category, each phrase must match the hint at the same index.

## Run on Windows PowerShell
1. Open PowerShell in this folder.
2. Create a virtual environment if needed: `py -m venv .venv`
3. Activate it: `\.venv\Scripts\Activate.ps1`
4. Install Flask: `python -m pip install -r requirements.txt`
5. Run: `python app.py`
6. Visit `http://127.0.0.1:5000`.

If `python` cannot be found, try `py app.py` or `\.venv\Scripts\python.exe app.py`.

## Run on Linux or macOS
1. Open Terminal in this folder.
2. Create a virtual environment if needed: `python3 -m venv .venv`
3. Activate it: `source .venv/bin/activate`
4. Install Flask: `python -m pip install -r requirements.txt`
5. Run: `python app.py`
6. Visit `http://127.0.0.1:5000`.

## Behavior
- Before START, all 52 tiles are green. No category, hint, guess controls, or counts appear below the board.
- START selects a random category, phrase, and matching hint.
- Phrase letters occupy white tiles; phrase spaces and unused tiles remain green. Tile sizes and spacing stay uniform.
- Correct consonants reveal all matching occurrences and earn $500 per occurrence.
- Previously guessed letters are displayed and cannot be guessed twice.

