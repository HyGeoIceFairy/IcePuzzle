import threading
import sys
import requests
import subprocess
import tkinter as tk
from tkinter import messagebox
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
import re

pattern = r"[\dM]-[\dM] [a-z]+"
ANSWERSHEET_URL = "https://raw.githubusercontent.com/HyGeoIceFairy/IcePuzzle/refs/heads/main/answersheet.json"


def create_image():
    image = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((4, 4, 28, 28), fill=(0, 100, 255))
    return image


def on_check_update(icon, item):
    def run_launcher():
        subprocess.run([sys.executable, "launcher.py"])

    threading.Thread(target=run_launcher, daemon=True).start()


def on_quit(icon, item):
    icon.stop()


def run_tray():
    icon = Icon("Checker", create_image(),
                menu=Menu(
                    MenuItem("Check Update", on_check_update),
                    MenuItem("Exit", on_quit)
    ))
    icon.run()


def getAnswersheet(question):
    try:
        r = requests.get(ANSWERSHEET_URL, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get(question)
    except Exception as e:
        return None


def main():
    threading.Thread(target=run_tray, daemon=True).start()
    print("This is Ice Puzzle checker. Input \"help\" for help.")
    while True:
        playerInput = input(">>>")
        if playerInput == "exit":
            sys.exit(0)
        elif playerInput == "help":
            print(
                "Input \"X-X [Answer]\" to check whether your answer is correct.\nInput \"exit\" to exit.")
        elif re.fullmatch(pattern, playerInput) is not None:
            answer = getAnswersheet(playerInput[:3])
            if answer == None:
                print(
                    "Failed to get correct answer. Please check whether both the input and the network are valid.")
            elif answer != playerInput[4:]:
                print("Wrong answer.")
            else:
                print("Correct. Congrats!")
        else:
            print("Invalid input. Please check your input.")


if __name__ == "__main__":
    main()
