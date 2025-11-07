from cli_main import start_cli
import subprocess
import sys
from pathlib import Path

def main():
    print("Choose the type of interface you would like to use now")
    print("g --- Graphical User Interface")
    print("c --- Command Line Interface")

    while True:
        choice = input("\nEnter your choice (g/c): ").strip().lower()

        if choice == "g":
            print("Starting GUI")
            here = Path(__file__).resolve().parent
            gui = here / "gui_main.py"
            subprocess.run([sys.executable, gui], check=True, cwd=str(here))
            break
        elif choice == "c":
            print("Starting CLI")
            start_cli()
            break
        else:
            print("\n Invalid input, please enter 'g' for GUI or 'c' for CLI\n")

if __name__ == "__main__":
    main()