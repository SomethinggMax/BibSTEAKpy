from nicegui import ui
import os
import json

import interface_handler
import utils.file_parser as file_parser
import re
import pprint
from objects import BibFile, Reference
from utils.abbreviations_exec import execute_abbreviations
from utils.file_parser import parse_bib
from utils.file_generator import generate_bib
from utils.merge import *
import subprocess
from merge_ui import Merge

files = {}
selected_file = None
selected_ref = None
selected_files: set[str] = set()
all_selected_files: bool = False
selected_references: set = set()
all_selected_references: bool = False
merge = None


PRIMARY_COLOR = "#CCE0D4"
SECONDARY_COLOR = "#9AC1A9"
SUCCESS_COLOR = "#5D9874"
# WARNING_COLOR = "#FBBF24"
# ERROR_COLOR = "#EF4444"


def config():
    config_path = "config.json"
    if not os.path.exists(config_path):
        with open(config_path, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def get_working_directory_path():
    config_file = config()
    return config_file.get("working_directory")
    

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
                ui.button(filename, on_click=lambda e, fn=filename: on_file_click(fn), color=SECONDARY_COLOR).classes(btn_classes).style("text-transform: none;")

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
            year = normalize_field(getattr(ref, 'year', None) or "N.D.")
            short_label = f"{author} ({year}): {title}"

            with ui.row().classes("items-center w-full gap-2"):
                checkbox = ui.checkbox(on_change=lambda e, r=ref: toggle_reference_selection(r, e.value)).style(f"accent-color: {SUCCESS_COLOR};")
                checkbox.value = ref in selected_references
                btn_classes = "flex-1 text-left"
                if ref is selected_ref:
                    btn_classes += " bg-gray-300"
                ui.button(short_label, on_click=lambda e, r=ref: on_ref_click(r), color = SECONDARY_COLOR).classes(btn_classes).style("text-transform: none;")


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
    global merge
    if not selected_files or len(selected_files) < 2:
        ui.notify("Please select at least two files to merge", color="red")
        return
    selected_files_list = list(selected_files)
    merge.start(selected_files_list, files, merge_files)

def _on_merge_done(merged_bib, selected_files_list):

    dialog = ui.dialog()
    with dialog, ui.card().classes("p-4 bg-gray-100 rounded shadow w-80"):
        ui.label("Enter a name for the merged file").classes("font-bold mb-2")
        name_input = ui.input(label="Merged file name").classes("w-full")
        def confirm():
            choose_merge_name(name_input.value, merged_bib, selected_files_list, dialog)
        with ui.row().classes("justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close, color=PRIMARY_COLOR).style("text-transform: none;")
            ui.button("Merge", on_click=confirm, color=SECONDARY_COLOR).style("text-transform: none;")
    dialog.open()
    
def _on_merge_error(msg: str):
    ui.notify(msg, color="red")

def choose_merge_name(name, merged_bib, selected_files_list, dialog):
    global selected_file, selected_ref, selected_files

    name = (name or "").strip()
    if not name:
        ui.notify("Please enter a name to merge the files", color="red")
        return

    merged_filename = name if name.endswith(".bib") else f"{name}.bib"
    save_bib_file(merged_filename, merged_bib)

    selected_file = merged_filename
    selected_ref = None
    selected_files = {merged_filename}

    dialog.close()
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
        ui.notify("Some references are selected, but filter will apply to all references in the file", color="orange")

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
            ui.button("Cancel", on_click=lambda: dialog.close(), color=PRIMARY_COLOR).style("text-transform: none;")
            def apply_sort():
                descending = order_dropdown.value == "Descending"
                order_by_field(bib_file, field_dropdown.value, descending=descending)
                populate_refs_for_file(selected_file)
                dialog.close()
                ui.notify(
                    f"References sorted by {field_dropdown.value} ({'descending' if descending else 'ascending'})"
                )
            ui.button("Apply", on_click=apply_sort, color=SECONDARY_COLOR).style("text-transform: none;")
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


def open_abbreviations_json():
    file_path = os.path.abspath("abbreviations.json")

    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump({}, f, indent=2)

    try:
        if os.name == "nt":
            os.startfile(file_path)
        elif os.name == "posix":
            subprocess.run(["xdg-open", file_path], check=False)
        else:
            ui.notify("Unsupported to open automatically", color="orange")
            return
        ui.notify("abbreviations.json is being opened", color="green")
    except Exception as e:
        ui.notify(f"Could not open file: {e}", color="red")


def save_settings(directory_input):
    path = directory_input.value.strip()
    if not path:
        ui.notify("Please enter a valid path.", color="red")
        return

    os.makedirs(path, exist_ok=True)
    config_path = "config.json"
    try:
        config_file = json.load(open(config_path)) if os.path.exists(config_path) else {}
    except json.JSONDecodeError:
        config_file = {}
    config_file["working_directory"] = path
    with open(config_path, "w") as f:
        json.dump(config_file, f, indent=2)

    ui.notify(f"Configuration saved! Directory: {path}", color="green")
    ui.timer(1.5, lambda: ui.run_javascript('window.location.href = "/"'))

@ui.page("/setup")
def setup_page():
    with ui.column().classes("items-center w-full"):
        ui.label("Setup").classes("text-4xl font-bold mb-4 mt-6 self-start ml-[400px]").style(f"color: {SUCCESS_COLOR};")

        with ui.column().classes("w-[700px] mx-auto p-6 bg-gray-100 rounded-2xl shadow-lg"):
            ui.label("Minimize or maximize").classes("font-bold text-lg mb-1 border-b-2 pb-1 w-full").style(f"border-color: {SECONDARY_COLOR};")
            with ui.row().classes("justify-start items-start w-full mb-6 mt-3 gap-10"):
                with ui.column().classes("gap-3"):
                    ui.checkbox("Abbreviate/expand").classes("text-md font-semibold").style(f"accent-color: {SUCCESS_COLOR};")
                    with ui.row().classes("items-center gap-2 ml-6"):
                        ui.image("icons/customize_rules.png").classes("w-7 h-7")
                        ui.button("Customize rules", color=SECONDARY_COLOR, on_click=open_abbreviations_json).classes("text-xs px-3 py-1 rounded-md").style("text-transform: none;")
                with ui.column().classes("gap-5 ml-30"):
                    ui.checkbox("Hide/unhide URL").classes("text-md font-semibold").style(f"accent-color: {SUCCESS_COLOR};")
                    ui.checkbox("Hide/unhide DOI").classes("text-md font-semibold").style(f"accent-color: {SUCCESS_COLOR};")

            ui.label("Merge Bib files").classes("font-bold text-lg mb-1 border-b-2 pb-1 w-full").style(f"border-color: {SECONDARY_COLOR};")
            with ui.column().classes("gap-3 mt-3 ml-2"):
                ui.checkbox("Utilize URL").classes("text-md font-semibold").style(f"accent-color: {SUCCESS_COLOR};")
                ui.checkbox("Utilize DOI").classes("text-md font-semibold").style(f"accent-color: {SUCCESS_COLOR};")

            ui.separator().classes("my-6")
            ui.label("Working Directory").classes("font-bold text-lg mb-2")
            directory_input = ui.input(label="Path to the working directory").classes("w-full")

        with ui.row().classes("justify-end mt-6"):
            ui.button("Save", color=SUCCESS_COLOR, on_click=lambda: save_settings(directory_input)).classes("px-6 py-2 rounded-lg font-semibold").style("text-transform: none;")

@ui.page('/')
def main_page():
    global files_col, refs_col, bib_col, merge

    wd = get_working_directory_path()
    if not wd:
        ui.notify("No working directory found. Please configure it first.", color="orange")
        ui.run_javascript('window.location.href = "/setup"')
        return

    load_all_files_from_storage()
    with ui.row().classes("w-full h-full gap-4 p-4 justify-between overflow-hidden"):
        files_col = ui.column().classes('p-4 bg-gray-100 rounded shadow overflow-y-auto w-[25%]')
        refs_col = ui.column().classes('p-4 bg-gray-100 rounded shadow overflow-y-auto w-[35%]')
        bib_col = ui.column().classes('p-4 bg-gray-100 rounded shadow overflow-y-auto w-[35%]')
    populate_files()

    merge = Merge(on_done=_on_merge_done, on_error=_on_merge_error)
    interface_handler.set_merge_object(merge)


def start_gui():
    ui.run()


if __name__ in {"__main__", "__mp_main__"}:
    start_gui()