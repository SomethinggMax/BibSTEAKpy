from nicegui import ui
import os
import json
import utils.file_parser as file_parser
import re
import pprint

files = {}
selected_file = None
selected_ref = None
selected_files: set[str] = set()
all_selected_files: bool = False
selected_references: set = set()
all_selected_references: bool = False

def get_working_directory_path():
    with open("config.json", "r") as f:
        config = json.load(f)
        working_directory_path = config["working_directory"]
        return working_directory_path
    

def load_all_files_from_storage():
    """
    Loads all of the files from the working directory 
    (the path is hard coded right now).
    """
    global files
    wd = get_working_directory_path()
    os.makedirs(wd, exist_ok=True)

    loaded = {}
    for filename in os.listdir(wd):
        if filename.endswith(".bib"):
            path = os.path.join(wd, filename)
            try:
                refs = file_parser.parse_bib(path, remove_whitespace_in_fields=True)
                loaded[filename] = refs
            except Exception as e:
                print(f"Error parsing {filename}: {e}")
                loaded[filename] = []
    files = loaded

def populate_files():

    """
    Populates the column for FILES with the FILES in 
    the directory and the corresponding buttons
    """
    files_col.clear()
    with files_col:
        with ui.row().classes("items-center justify-between w-full"):
            # the header of the files column
            ui.label("Files").classes("font-bold text-lg")

            with ui.column().classes("items-center gap-1"):
                ui.image("select.png") \
                    .classes("w-8 h-8 cursor-pointer") \
                    .on("click", toggle_select_all_files)
                ui.label("Select All").classes("font-bold text-xs")

        if not files:
            ui.label("(no .bib files found)")

        #display of selection choice (using checkboxes)    
        for filename in files:
            with ui.row().classes("items-center w-full gap-2"):
                checkbox = ui.checkbox(on_change=lambda e, fn=filename: toggle_file_selection(fn, e.value))
                checkbox.value = filename in selected_files

                btn_classes = "flex-1 text-left"
                if filename == selected_file:
                    btn_classes += " bg-gray-300"
                ui.button(filename, on_click=lambda e, fn=filename: on_file_click(fn)).classes(btn_classes)


def toggle_file_selection(filename: str, checked: bool):
    """
    Toggles the selection for the FILES in the FILES column
    """
    if checked:
        selected_files.add(filename)
    else:
        selected_files.discard(filename)


def toggle_select_all_files():
    """
    Toggles the selection for ALL of the FILES in the FILES column
    """
    global selected_files, all_selected_files
    if all_selected_files:
        # Deselect all
        selected_files.clear()
        all_selected_files = False
    else:
        # Select all
        selected_files = set(files.keys())
        all_selected_files = True

    populate_files()


def normalize_field(value: str) -> str:
    if not value:
        return "?"
    normalized = re.sub(r"[{}]", "", value)
    normalized = re.sub(r"\\[a-zA-Z]+\s*", "", normalized)
    normalized = re.sub(r"\\['\"`^~=.]", "", normalized)
    normalized = " ".join(normalized.split())
    return normalized.strip()


def populate_refs_for_file(filename: str):
    """
    Populates the column for REFERENCES with the REFERENCES in 
    the file and the corresponding buttons
    """
    refs_col.clear()
    with refs_col:
        with ui.row().classes("items-center justify-between w-full"):
            ui.label("References").classes("font-bold text-lg")

            with ui.column().classes("items-center gap-1"):
                ui.image("select.png") \
                    .classes("w-8 h-8 cursor-pointer") \
                    .on("click", lambda: toggle_select_all_references(filename))
                ui.label("Select All").classes("font-bold text-xs")

        for ref in files[filename].references:
            author = normalize_field(getattr(ref, 'author', None) or "Unknown Author")
            title = normalize_field(getattr(ref, 'title', None) or "Untitled")
            year = normalize_field(getattr(ref, 'year', None) or "n.d.")
            short_label = f"{author} ({year}): {title}"

            with ui.row().classes("items-center w-full gap-2"):
                checkbox = ui.checkbox(on_change=lambda e, r=ref: toggle_reference_selection(r, e.value))
                checkbox.value = ref in selected_references

                btn_classes = "flex-1 text-left"
                if ref is selected_ref:
                    btn_classes += " bg-gray-300"
                ui.button(short_label, on_click=lambda e, r=ref: on_ref_click(r)).classes(btn_classes)


def toggle_reference_selection(ref, checked: bool):
    """
    Toggles the selection for the REFERENCES in the REFERENCES column
    """
    if checked:
        selected_references.add(ref)
    else:
        selected_references.discard(ref)


def toggle_select_all_references(filename: str):
    """
    Toggles the selection for ALL of the REFERENCES in the REFERENCES column
    """
    global selected_references, all_selected_references
    refs = files[filename].references
    if all_selected_references:
        # Deselect all
        selected_references.clear()
        all_selected_references = False
    else:
        # Select all
        selected_references = set(refs)
        all_selected_references = True

    populate_refs_for_file(filename)


def populate_bib_for_ref(ref):
    """
    Populates the column for BIB content with the bib of the 
    reference in the file and the corresponding buttons
    """
    bib_col.clear()
    with bib_col:
        ui.label("BibTeX Content").classes("font-bold text-lg")
        try:
            if hasattr(ref, "to_bibtex"):
                entry = ref.to_bibtex()
            else:
                entry = pprint.pformat(ref.__dict__, sort_dicts=False)
        except Exception as e:
            entry = f"% ERROR converting Reference: {e}\n{ref}"

        ui.code(entry, language="bibtex").classes(
            "text-sm w-full whitespace-pre-wrap break-words"
        )


def on_file_click(filename: str):
    """
    Toggles the display of the REFERENCE column with 
    the references from the file that was clicked
    """
    global selected_file, selected_ref
    selected_file = filename
    selected_ref = None
    populate_files()
    refs_col.clear()
    bib_col.clear()
    populate_refs_for_file(filename)


def on_ref_click(ref: dict):
    """
    Toggles the display of the BIB column with the bib content 
    from the reference from the file that was clicked
    """
    global selected_ref
    selected_ref = ref
    populate_refs_for_file(selected_file)
    populate_bib_for_ref(ref)


@ui.page('/')
def main_page():
    """
    Handles the creation of the columns: FILES, REFERENCES and BIBTEX CONTENT
    """
    global files_col, refs_col, bib_col
    load_all_files_from_storage()
    with ui.row().classes('w-full h-full gap-4 p-4'):
        files_col = ui.column().classes('p-4 bg-gray-100 rounded shadow w-64')
        refs_col = ui.column().classes('p-4 bg-gray-200 rounded shadow flex-1 min-w-[360px]')
        bib_col = ui.column().classes('p-4 bg-gray-300 rounded shadow flex-1 min-w-[360px]')
    populate_files()


ui.run()
