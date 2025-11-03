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


def print_msg(text: str):
    show_lines([text])


def show_lines(lines: list[str]):
    if user_interface == "CLI":
        # Print the prompt
        for line in lines:
            print(line)
    elif user_interface == "GUI":
        for line in lines:
            merge_object.print_hook(line)


def show_toast(msg: str, level: str = "info"):
    if user_interface == "CLI":
        print_msg(msg)
    elif user_interface == "GUI":
        if hasattr(merge_object, 'toast_hook'):
            merge_object.toast_hook(msg, level)
        else:
            merge_object.print_hook(msg)


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


def prompt_reference_comparison(ref1_text: str, ref2_text: str, header: str = "Possible duplicate references", option1: str = "Merge references", option2: str = "Keep both") -> int:
    if user_interface == "CLI":
        print_msg(colorize(header, 'bold'))
        print_msg(colorize("Reference 1:", 'dim'))
        show_lines([ref1_text])
        print_msg(colorize("Reference 2:", 'dim'))
        show_lines([ref2_text])
        return get_selection("Enter your choice (1 or 2): ", 2)
    elif user_interface == "GUI":
        resp = merge_object.prompt_reference_comparison(header, ref1_text, ref2_text, option1, option2)
        return 1 if str(resp).strip() == '1' else 2


def prompt_field_conflict(field_name: str, value1: str, value2: str, header: str | None = None) -> int:
    title = header or f"Conflict in field '{field_name}'"
    if user_interface == "CLI":
        print_msg(colorize(title, 'bold'))
        print_msg(colorize("1. Value from reference 1:", 'dim'))
        show_lines([value1])
        print_msg(colorize("2. Value from reference 2:", 'dim'))
        show_lines([value2])
        return get_selection("Choose which to keep (1 or 2): ", 2)
    elif user_interface == "GUI":
        resp = merge_object.prompt_field_conflict(title, value1, value2)
        return 1 if str(resp).strip() == '1' else 2


def prompt_abbreviation_conflict(long1: str, long2: str, abbr: str) -> int:
    header = f"Conflict with string abbreviation '{abbr}'!"
    if user_interface == "CLI":
        show_lines([header, "You can select an abbreviation to rename.", f"1: {long1}", f"2: {long2}"])
        return get_selection("Enter your choice (1 or 2): ", 2)
    elif user_interface == "GUI":
        resp = merge_object.prompt_abbreviation_conflict(header, long1, long2)
        return 1 if str(resp).strip() == '1' else 2


def prompt_text_input(prompt: str, default: str = "") -> str:
    if user_interface == "CLI":
        return input(prompt)
    elif user_interface == "GUI":
        return merge_object.prompt_text_input(prompt, default)
