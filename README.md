## How to use it
Just do ```python CLI.py``` in the CMD or PowerShell to start the shell 

Then set up your working directory using the ```set_directory <absolte/path/to/wd>``` command and add the ABSOLUTE path to a directory on your computer. Later, we will add a GUI to select the path with the File Explorer.

All the available commands can be seen by using the ```help``` command

Note that to see the changes, you can view the content of any file from your working directory directly into the CLI by using the ```view <filename.bib>``` command
## Installation
Linux: python3.12-venv needs installation
Execute install_bibsteak.sh

## Uninstall
rm -rf ~/.local/opt/BibSTEAKpy
rm -f ~/.local/bin/bibsteak
## Extra
You can do ```pip install pyreadline3``` to enable custom CLI auto-completions with tab. For now, just do it globally instead of using a venv.

