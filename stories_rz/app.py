import os
import secrets
import sys
from pathlib import Path

from flask import Flask, redirect, render_template, request, session, url_for

ROOT = Path(__file__).resolve().parent
# The game logic lives in the wheel_of_fortune package one folder up. Putting the
# repo root on the path lets `python app.py` work from inside this folder too.
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

from wheel_of_fortune import (  # noqa: E402
    BOARD_ROWS,
    MAX_PLAYERS,
    MIN_PLAYERS,
    WedgeType,
    Wheel,
    arrange_words,
    clean_names,
    create_wheel,
    load_puzzle,
    next_turn,
    play_order,
)

app = Flask(__name__)
# Set WOF_SECRET_KEY to keep sessions valid across restarts; otherwise each run gets a fresh key.
app.secret_key = os.environ.get("WOF_SECRET_KEY") or secrets.token_hex(32)

VOWEL_COST = 250


def current_player():
    return session["players"][session["turn"]]


def start_round(round_number):
    """New puzzle and a new wheel for the round. The starting player rotates each round."""
    session["game"] = load_puzzle()
    session["round_number"] = round_number
    session["wheel"] = create_wheel(round_number).to_dict()
    session["turn"] = (round_number - 1) % len(session["players"])
    session["guessed_letters"] = []
    session["winner"] = None
    session["current_spin"] = None
    session["can_guess"] = False


def pass_turn():
    """Hand play to the next player, dropping any unused spin. Returns their name."""
    session["turn"] = next_turn(session["turn"], len(session["players"]))
    session["current_spin"] = None
    session["can_guess"] = False
    return current_player()


def set_money(player_index, amount):
    money = list(session["money"])
    money[player_index] = amount
    session["money"] = money


def add_money(amount):
    set_money(session["turn"], session["money"][session["turn"]] + amount)


def round_active():
    return bool(session.get("game")) and session.get("winner") is None


def win_round():
    session["winner"] = session["turn"]
    session["current_spin"] = None
    session["can_guess"] = False


def puzzle_complete():
    letters = {c for c in session["game"]["answer"] if c.isalpha()}
    return letters.issubset(session.get("guessed_letters", []))


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "start":
            try:
                names = clean_names(request.form.getlist("player"))
            except ValueError as error:
                session["message"] = str(error)
                return redirect(url_for("index"))

            session["players"] = play_order(names)
            session["money"] = [0] * len(names)
            start_round(1)
            session["message"] = f"Puzzle selected. {current_player()}, spin the wheel to begin!"
            return redirect(url_for("index"))

        if action == "spin" and round_active():
            if session.get("can_guess"):
                session["message"] = "You already spun. Guess a consonant before spinning again."
                return redirect(url_for("index"))

            # Spin the wheel built for this round, not a fresh one, and remember where it stopped.
            wheel = Wheel.from_dict(session["wheel"])
            result = wheel.spin()
            session["wheel"] = wheel.to_dict()

            message = result.message()

            if result.wedge.kind == WedgeType.BANKRUPT:
                set_money(session["turn"], 0)
                session["message"] = f"{message} {pass_turn()}, you're up."
            elif result.wedge.kind == WedgeType.LOSE_A_TURN:
                session["message"] = f"{message} {pass_turn()}, you're up."
            else:
                session["current_spin"] = result.value
                session["can_guess"] = True
                session["message"] = message

            return redirect(url_for("index"))

        if action == "guess" and round_active():
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
                session["guessed_letters"] = session.get("guessed_letters", []) + [letter]

                answer = session["game"]["answer"]
                count = answer.count(letter)

                if count:
                    earned = count * spin_val
                    add_money(earned)
                    session["current_spin"] = None
                    session["can_guess"] = False
                    session["message"] = f"Correct! {letter} appears {count} time(s). You earned ${earned:,}."
                    if puzzle_complete():
                        win_round()
                        session["message"] += f" {current_player()} revealed the last letter and wins the round!"
                else:
                    session["message"] = f"There is no {letter} in the phrase. {pass_turn()}, you're up."

            return redirect(url_for("index"))

        if action == "buy_vowel" and round_active():
            letter = request.form.get("vowel", "").strip().upper()
            money = session["money"][session["turn"]]

            if money < VOWEL_COST:
                session["message"] = f"You need at least ${VOWEL_COST} to buy a vowel."
            elif letter not in "AEIOU" or len(letter) != 1:
                session["message"] = "Please enter a valid vowel (A, E, I, O, U)."
            elif letter in session.get("guessed_letters", []):
                session["message"] = f"The vowel '{letter}' has already been guessed."
            else:
                add_money(-VOWEL_COST)
                session["guessed_letters"] = session.get("guessed_letters", []) + [letter]

                count = session["game"]["answer"].count(letter)

                if count:
                    session["message"] = f"Purchased '{letter}'! Revealed {count} occurrence(s)."
                    if puzzle_complete():
                        win_round()
                        session["message"] += f" {current_player()} revealed the last letter and wins the round!"
                else:
                    session["message"] = f"No '{letter}'s found in the puzzle. {pass_turn()}, you're up."

            return redirect(url_for("index"))

        if action == "solve" and round_active():
            solution = request.form.get("solution", "").strip().upper()
            answer = session["game"]["answer"]

            if not solution:
                session["message"] = "Type your solution first."
            elif solution == answer:
                win_round()
                session["message"] = (
                    f"🎉 CORRECT! {current_player()} solved the puzzle and won "
                    f"${session['money'][session['turn']]:,}!"
                )
            else:
                session["message"] = f"'{solution}' is incorrect! {pass_turn()}, you're up."

            return redirect(url_for("index"))

        if action == "next_round" and session.get("game") and session.get("winner") is not None:
            start_round(session["round_number"] + 1)
            session["message"] = f"Round {session['round_number']}. {current_player()}, spin the wheel to begin!"
            return redirect(url_for("index"))

    game = session.get("game")
    board_letters = arrange_words(game["answer"], BOARD_ROWS) if game else []
    players = session.get("players", [])
    winner = session.get("winner")
    scoreboard = [
        {"name": name, "money": money, "current": game is not None and i == session.get("turn")}
        for i, (name, money) in enumerate(zip(players, session.get("money", [])))
    ]

    return render_template(
        "index.html",
        game=game,
        board_rows=BOARD_ROWS,
        board_letters=board_letters,
        guessed_letters=session.get("guessed_letters", []),
        scoreboard=scoreboard,
        player_names=players,
        min_players=MIN_PLAYERS,
        max_players=MAX_PLAYERS,
        round_number=session.get("round_number", 1),
        current_spin=session.get("current_spin"),
        can_guess=session.get("can_guess", False),
        message=session.get("message", ""),
        solved=winner is not None,
        winner_name=players[winner] if winner is not None else None,
        vowel_cost=VOWEL_COST,
    )


@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
