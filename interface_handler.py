def show_lines(lines: [str]):
    # Print the prompt
    for line in lines:
        print(line)


def get_selection(prompt: str, number_of_options: int) -> int:
    """
    Gets user input for a specific prompt.
    :param prompt: The prompt to ask the user for the input.
    :param number_of_options: The number of options the user can choose.
    :return: the choice as an integer.
    """
    while True:
        choice = input(prompt)
        try:
            choice = int(choice)
            if choice < 1 or choice > number_of_options:
                raise ValueError
            return choice
        except ValueError:
            print(f"Invalid input: input an integer in the range from 1 to {number_of_options}")


def get_input(prompt: str) -> str:
    """
    Get input from the user.
    :param prompt: The prompt to ask the user for the input.
    :return: the input from the user.
    """
    user_input = input(prompt)
    return user_input
