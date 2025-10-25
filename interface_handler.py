import os
import sys
from utils import json_loader

ANSI = {
    'reset': '\x1b[0m',
    'dim': '\x1b[2m',
    'bold': '\x1b[1m',
    'red': '\x1b[31m',
    'green': '\x1b[32m',
    'yellow': '\x1b[33m',
}

config = json_loader.load_config()
user_interface = config.get("user_interface", "CLI")

merge_object = None


def set_merge_object(obj):
    global merge_object
    merge_object = obj
    merge_object.init_ui()


def supports_color() -> bool:
    try:
        return sys.stdout.isatty() and not os.environ.get('NO_COLOR')
    except Exception:
        return False


def colorize(text: str, color: str) -> str:
    if not supports_color() or color not in ANSI:
        return text
    return f"{ANSI[color]}{text}{ANSI['reset']}"


def show_lines(lines: [str]):
    if user_interface == "CLI":
        # Print the prompt
        for line in lines:
            print(line)
    elif user_interface == "GUI":
        for line in lines:
            merge_object.print_hook(line)


def get_selection(prompt: str, number_of_options: int) -> int:
    """
    Gets user input for a specific prompt.
    :param prompt: The prompt to ask the user for the input.
    :param number_of_options: The number of options the user can choose.
    :return: the choice as an integer.
    """
    if user_interface == "CLI":
        while True:
            choice = input(prompt)
            try:
                choice = int(choice)
                if choice < 1 or choice > number_of_options:
                    raise ValueError
                return choice
            except ValueError:
                print(f"Invalid input: input an integer in the range from 1 to {number_of_options}")
    elif user_interface == "GUI":
        if merge_object is not None:
            return merge_object.input_hook(prompt)


def get_input(prompt: str) -> str:
    """
    Get input from the user.
    :param prompt: The prompt to ask the user for the input.
    :return: the input from the user.
    """
    if user_interface == "CLI":
        user_input = input(prompt)
    elif user_interface == "GUI":
        user_input = merge_object.input_hook(prompt)
    return user_input
