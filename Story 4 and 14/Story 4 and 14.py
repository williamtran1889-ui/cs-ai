#library
import random
import time
import json


#player
player_count = 0
while player_count < 2 or player_count > 5:
    player_count = int(input("How many players will be player? (between 2 and 5):"))
    if player_count < 2 or player_count > 5:
        print("error")

players_list = []
for i in range(player_count):
    name = input("Enter name for player:")
    players_list.append(name)

print("List of players:", players_list)


#4 - Proper player to be promoted and allowed to take a turn so that game proceeds in an orderly and fair manner
print("Determining player playing order")
random.shuffle(players_list)

turn = 0 #points at the position in the lis
for round_number in range(6):
    current_player = players_list[turn]
    print("turn:", current_player)
    turn = turn + 1
    if turn == len(players_list):
        turn = 0




#14 - toss up questions to be displayed letter by letter until a player buzzes in that they have an answer
#the phrase as blanks
with open("phrases.json", "r") as file:
    data = json.load(file)

Phrase = random.choice(random.choice(data["phrases"]))

display = ""
for letter in Phrase:
    if letter == " ":
        display = display + "  "
    else:
        display = display + "_ "   # added a space so the blanks don't run together
print(display)

#change display loop and reveal what to show
positions = []  #reveal one letter at a time, not just position 0
for i in range(len(Phrase)):
    if Phrase[i] != " ":
        positions.append(i)
random.shuffle(positions)

shown = []
print("Press Ctrl+C to buzz in")
try:
    for pos in positions:
        shown.append(pos)

        display = ""
        for i in range(len(Phrase)):
            if Phrase[i] == " ":
                display = display + "  "
            elif i in shown:
                display = display + Phrase[i] + " "
            else:
                display = display + "_ " 
        print(display)
        time.sleep(1) #one letter per second
    print("nobody got the answer, phrase was:", Phrase)

except KeyboardInterrupt:
    print("\nBuzz!")
    answer = input("Your Answer: ")

    if answer.strip().upper() == Phrase:
        print("Bingo! Correct")
    else:
        print("Wrong! The phrase was:", Phrase)
