import json
import random
from pathlib import Path
from flask import Flask, redirect, render_template, request, session, url_for
from wheel_of_fortune.wheel import create_wheel, WedgeType

app = Flask(__name__)
app.secret_key = "replace-this-with-a-random-secret-key"
ROOT = Path(__file__).resolve().parent

BOARD_ROWS = [12, 14, 14, 12]
VOWEL_COST = 250


def load_json(filename):
    with (ROOT / filename).open(encoding="utf-8") as f:
        return json.load(f)


def load_puzzle():
    categories = load_json("categories.json")["categories"]
    phrases = load_json("phrases.json")["phrases"]
    hints = load_json("hints.json")["hints"]

    if not (len(categories) == len(phrases) == len(hints)):
        raise ValueError("JSON category counts must match.")
    
    ci = random.randrange(len(categories))
    if len(phrases[ci]) != len(hints[ci]) or not phrases[ci]:
        raise ValueError("Each phrase must have a matching hint.")
    
    pi = random.randrange(len(phrases[ci]))
    answer = phrases[ci][pi].strip().upper()

    if len(answer) > sum(BOARD_ROWS):
        raise ValueError("Phrase must fit in the 52-tile board.")
    
    return {"category": categories[ci], "answer": answer, "hint": hints[ci][pi]}


def arrange_words(answer, board_rows):
    rows = [[] for _ in board_rows]
    row_index = 0

    for word in answer.split():
        if row_index >= len(board_rows):
            break

        while (
            row_index < len(board_rows)
            and sum(len(w) for w in rows[row_index]) + len(rows[row_index]) + len(word) > board_rows[row_index]
        ):
            row_index += 1

        if row_index >= len(board_rows):
            break

        rows[row_index].append(list(word))

    return rows


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "start":
            session["game"] = load_puzzle()
            session["round_number"] = 1
            session["guessed_letters"] = []
            session["revealed_positions"] = []
            session["money"] = 0
            session["current_spin"] = None
            session["can_guess"] = False
            session["message"] = "Puzzle selected. Spin the wheel to begin!"
            return redirect(url_for("index"))

        if action == "spin" and session.get("game"):
            round_num = session.get("round_number", 1)
            wheel = create_wheel(round_num)
            result = wheel.spin()
            
            session["message"] = result.message()

            if result.wedge.kind == WedgeType.BANKRUPT:
                session["money"] = 0
                session["current_spin"] = None
                session["can_guess"] = False
            elif result.wedge.kind == WedgeType.LOSE_A_TURN:
                session["current_spin"] = None
                session["can_guess"] = False
            else:
                session["current_spin"] = result.value
                session["can_guess"] = True

            return redirect(url_for("index"))

        if action == "guess" and session.get("game"):
            letter = request.form.get("letter", "").strip().upper()
            spin_val = session.get("current_spin")

            if not spin_val or not session.get("can_guess"):
                session["message"] = "Please spin the wheel before guessing a consonant!"
            elif len(letter) != 1 or not letter.isalpha():
                session["message"] = "Enter one letter."
            elif letter in "AEIOU":
                session["message"] = "Please guess a consonant, not a vowel. Use 'Buy Vowel' for vowels."
            elif letter in session.get("guessed_letters", []):
                session["message"] = f"You already guessed {letter}."
            else:
                guesses = session.get("guessed_letters", [])
                guesses.append(letter)
                session["guessed_letters"] = guesses

                answer = session["game"]["answer"]
                matches = [i for i, char in enumerate(answer) if char == letter]

                if matches:
                    positions = session.get("revealed_positions", []) + matches
                    session["revealed_positions"] = sorted(set(positions))
                    earned = len(matches) * spin_val
                    session["money"] = session.get("money", 0) + earned
                    session["message"] = f"Correct! {letter} appears {len(matches)} time(s). You earned ${earned:,}."
                else:
                    session["message"] = f"There is no {letter} in the phrase."
                
                # Reset spin after guess attempt
                session["current_spin"] = None
                session["can_guess"] = False

            return redirect(url_for("index"))

        if action == "buy_vowel" and session.get("game"):
            letter = request.form.get("vowel", "").strip().upper()
            money = session.get("money", 0)

            if money < VOWEL_COST:
                session["message"] = f"You need at least ${VOWEL_COST} to buy a vowel."
            elif letter not in "AEIOU" or len(letter) != 1:
                session["message"] = "Please enter a valid vowel (A, E, I, O, U)."
            elif letter in session.get("guessed_letters", []):
                session["message"] = f"The vowel '{letter}' has already been guessed."
            else:
                session["money"] -= VOWEL_COST
                guesses = session.get("guessed_letters", [])
                guesses.append(letter)
                session["guessed_letters"] = guesses

                answer = session["game"]["answer"]
                matches = [i for i, char in enumerate(answer) if char == letter]

                if matches:
                    positions = session.get("revealed_positions", []) + matches
                    session["revealed_positions"] = sorted(set(positions))
                    session["message"] = f"Purchased '{letter}'! Revealed {len(matches)} occurrence(s)."
                else:
                    session["message"] = f"No '{letter}'s found in the puzzle."

            return redirect(url_for("index"))

        if action == "solve" and session.get("game"):
            solution = request.form.get("solution", "").strip().upper()
            answer = session["game"]["answer"]

            if solution == answer:
                session["revealed_positions"] = list(range(len(answer)))
                session["message"] = f"🎉 CORRECT! You solved the puzzle and won ${session.get('money', 0):,}!"
            else:
                session["message"] = f"'{solution}' is incorrect! Keep playing."

            return redirect(url_for("index"))

    game = session.get("game")
    board_letters = arrange_words(game["answer"], BOARD_ROWS) if game else []
    
    solved = False
    if game:
        unique_letters = set(c for c in game["answer"] if c.isalpha())
        guessed_set = set(session.get("guessed_letters", []))
        solved = unique_letters.issubset(guessed_set)

    return render_template(
        "index.html", 
        game=game, 
        board_rows=BOARD_ROWS,
        board_letters=board_letters,
        revealed_positions=session.get("revealed_positions", []),
        guessed_letters=session.get("guessed_letters", []),
        money=session.get("money", 0), 
        current_spin=session.get("current_spin"),
        can_guess=session.get("can_guess", False),
        message=session.get("message", ""),
        solved=solved,
        vowel_cost=VOWEL_COST
    )

@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)