from nicegui import ui
import os
import json
import utils.file_parser as file_parser
import re
import pprint
from objects import BibFile, Reference, String, Comment, Preamble
import utils.batch_editor as batch_editor
from utils.abbreviations_exec import execute_abbreviations
from utils.file_parser import parse_bib
from utils.file_generator import generate_bib
from utils.merge import *

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
                bib_file = file_parser.parse_bib(path, remove_whitespace_in_fields=True)
                loaded[filename] = bib_file
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
        with ui.row().classes("items-center justify-between w-full mb-5"):
            # the header of the files column
            ui.label("Files").classes("font-bold text-lg")
            #display of the select all button
            with ui.column().classes("items-center gap-1"):
                ui.image("icons/select.png").classes("w-6 h-6 cursor-pointer").on("click", toggle_select_all_files)
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

        #display of the bar at the bottom
        with files_col:
            with ui.row().classes("items-center justify-between p-5 bg-gray-200 rounded-lg shadow-inner w-full mt-10"):
                with ui.column().classes("items-center gap-1"):
                    ui.image("icons/merge.png").classes("w-5 h-5 cursor-pointer").on("click", on_merge_click)
                    ui.label("Merge").classes("font-bold text-xs")
                with ui.column().classes("items-center gap-1"):
                    ui.image("icons/minimize.png").classes("w-5 h-5 cursor-pointer").on("click", on_minimize_click)
                    ui.label("Minimize").classes("font-bold text-xs")
                with ui.column().classes("items-center gap-1"):
                    ui.image("icons/maximize.png").classes("w-5 h-5 cursor-pointer").on("click", on_maximize_click)
                    ui.label("Maximize").classes("font-bold text-xs")
                with ui.column().classes("items-center gap-1"):
                    ui.image("icons/batchReplace.png").classes("w-5 h-5 cursor-pointer mt-1").on("click")
                    ui.label("Batch\nReplace").classes("font-bold text-xs text-center whitespace-pre-line")



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
        with ui.row().classes("items-center justify-between w-full mb-5"):
            ui.label("References").classes("font-bold text-lg")
            with ui.row().classes("items-center gap-4"):
                with ui.column().classes("items-center gap-1"):
                    ui.image("icons/tag.png").classes("w-6 h-6 cursor-pointer").on("click")
                    ui.label("Tag").classes("font-bold text-xs")
                with ui.column().classes("items-center gap-1"):
                    ui.image("icons/filter.png").classes("w-6 h-6 cursor-pointer").on("click", on_filter_click)
                    ui.label("Filter").classes("font-bold text-xs")
                with ui.column().classes("items-center gap-1"):
                    ui.image("icons/select.png").classes("w-6 h-6 cursor-pointer").on("click", lambda: toggle_select_all_references(filename))
                    ui.label("Select All").classes("font-bold text-xs")

        bib_file = files[filename]

        for ref in [r for r in bib_file.content if isinstance(r, Reference)]:
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
    bib_file = files[filename]
    refs = [r for r in bib_file.content if isinstance(r, Reference)]
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
        with ui.row().classes("items-center justify-between w-full mb-5 mt-2"):
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

def on_minimize_click():
    if not selected_files:
        ui.notify("Please select at least one file to minimize", color="red")
        return

    for filename in selected_files:
        bib_file = files[filename]
        updated_bib = execute_abbreviations(bib_file, minimize=True, max_abbreviations=9999)
        save_bib_file(filename, updated_bib)

    ui.notify(f"Minimized abbreviations for {len(selected_files)} file(s)", color="green")
    reload_after_edit()


def on_maximize_click():
    if not selected_files:
        ui.notify("Please select at least one file to maximize", color="red")
        return

    for filename in selected_files:
        bib_file = files[filename]
        updated_bib = execute_abbreviations(bib_file, minimize=False, max_abbreviations=9999)
        save_bib_file(filename, updated_bib)

    ui.notify(f"Maximized abbreviations for {len(selected_files)} file(s)", color="green")
    reload_after_edit()

def on_merge_click():
    global selected_file, selected_ref, selected_files
    if not selected_files or len(selected_files) < 2:
        ui.notify("Please select at least two files to merge", color="red")
        return
    selected_files_list = list(selected_files)
    merged_bib = files[selected_files_list[0]]

    for filename in selected_files_list[1:]:
        bib_to_merge = files[filename]
        merged_bib = merge_files(merged_bib, bib_to_merge)

    merged_filename = "+".join(selected_files_list)
    save_bib_file(merged_filename, merged_bib)

    selected_file = merged_filename
    selected_ref = None
    selected_files = {merged_filename}

    ui.notify(f"Merged {len(selected_files_list)} files into '{merged_filename}'", color="green")
    reload_after_edit()


def on_filter_click():
    if not selected_file:
        ui.notify("Please select a file first", color="red")
        return

    bib_file = files[selected_file]
    references = [r for r in bib_file.content if isinstance(r, Reference)]

    num_selected = len(selected_references)
    total_refs = len(references)

    if 0 < num_selected < total_refs:
        ui.notify(
            "Some references are selected, but filter will apply to all references in the file", 
            color="orange"
        )

    with ui.dialog() as dialog, ui.card().classes("p-4 bg-gray-100 rounded shadow w-64"):
        ui.label("Sort References").classes("font-bold text-lg mb-2")
        field_dropdown = ui.select(
            options=["author", "title", "year"],
            value="author",
            label="Sort by"
        )
        order_dropdown = ui.select(
            options=["Ascending", "Descending"],
            value="Ascending",
            label="Order"
        )
        with ui.row().classes("justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=lambda: dialog.close())
            def apply_sort():
                descending = order_dropdown.value == "Descending"
                order_by_field(bib_file, field_dropdown.value, descending=descending)
                populate_refs_for_file(selected_file)
                dialog.close()
                ui.notify(
                    f"References sorted by {field_dropdown.value} ({'descending' if descending else 'ascending'})"
                )
            ui.button("Apply", on_click=apply_sort)
    dialog.open()
    

def order_by_field(file: BibFile, field: str, descending=False):
    references = [ref for ref in file.content if isinstance(ref, Reference)]
    
    def get_field_safe(ref, field):
        value = getattr(ref, field, None)
        return value if value is not None else ""
    
    sorted_refs = sorted(references, key=lambda ref: get_field_safe(ref, field), reverse=descending)
    remaining_entries = [e for e in file.content if not isinstance(e, Reference)]
    file.content = remaining_entries + sorted_refs


def save_bib_file(filename: str, bib_file):

    wd = get_working_directory_path()
    path = os.path.join(wd, filename)
    try:
        ALIGN_FIELDS_POSITION = 15
        generate_bib(bib_file, path, ALIGN_FIELDS_POSITION)
        files[filename] = parse_bib(path, remove_whitespace_in_fields=True)
        print(f"Saved {filename} successfully")
        ui.notify(f"Saved {filename} successfully", color="green")
    except Exception as e:
        print(f"Error saving {filename}: {e}")
        ui.notify(f"Error saving {filename}: {e}", color="red")

def reload_after_edit():
    global selected_file, selected_ref
    load_all_files_from_storage()
    populate_files()
    # if a file is selected, reload the references
    if selected_file and selected_file in files:
        populate_refs_for_file(selected_file)
        # if a reference is being edited, reload the bib content too
        if selected_ref:
            # matching by cite_key
            new_refs = [r for r in files[selected_file].content if isinstance(r, Reference)]
            matched_ref = next((r for r in new_refs if r.cite_key == selected_ref.cite_key), None)
            if matched_ref:
                selected_ref = matched_ref
                populate_bib_for_ref(selected_ref)
            else:
                selected_ref = None

@ui.page('/')
def main_page():
    """
    Handles the creation of the columns: FILES, REFERENCES and BIBTEX CONTENT
    """
    global files_col, refs_col, bib_col
    load_all_files_from_storage()
    with ui.column().classes("w-full h-full"):
        with ui.row().classes('w-full h-full gap-4 p-4'):
            files_col = ui.column().classes('p-4 bg-gray-100 rounded shadow w-90')
            refs_col = ui.column().classes('p-4 bg-gray-200 rounded shadow flex-1 min-w-[360px]')
            bib_col = ui.column().classes('p-4 bg-gray-300 rounded shadow flex-1 min-w-[360px]')
    populate_files()


def start_gui():
    ui.run()

if __name__ in {"__main__", "__mp_main__"}:
    start_gui()
