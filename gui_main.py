from nicegui import ui, app
import os, re, json, pprint, asyncio, threading, subprocess, interface_handler
from merge_ui import Merge
from objects import BibFile
from utils import json_loader, cleanup, filtering, enrichment
from utils.merge import *
import utils.file_parser as file_parser
from utils.file_parser import parse_bib
from utils.file_generator import generate_bib
from utils.abbreviations_exec import execute_abbreviations
from utils.tagging import tag_refs
from history_manager import undo, redo



files = {}
selected_file = None
selected_ref = None
selected_files: set[str] = set()
all_selected_files: bool = False
selected_references: set = set()
all_selected_references: bool = False
merge = None
connected_users = 0
search_active = False
search_results = []
search_term = None


PRIMARY_COLOR = "#CCE0D4"
SECONDARY_COLOR = "#9AC1A9"
SUCCESS_COLOR = "#5D9874"
SELECTED_COLOR = "#588F6D"



def is_reference(entry) -> bool:
    return hasattr(entry, 'cite_key') and hasattr(entry, 'entry_type')

def iter_references(bib_file) -> list:
    return [e for e in getattr(bib_file, 'content', []) if is_reference(e)]


def load_all_files_from_storage():
    """
    Loads all of the files from the working directory 
    (the path is hard coded right now).
    """
    global files

    try:
        wd = json_loader.get_wd_path()
    except Exception:
        files = {}
        return
    
    os.makedirs(wd, exist_ok=True)

    loaded = {}
    for filename in os.listdir(wd):
        if filename.endswith(".bib"):
            path = os.path.join(wd, filename)
            try:
                bib_file = file_parser.parse_bib(path)
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
        with ui.row().classes("items-center justify-between w-full mb-2"):
            # the header of the files column
            ui.label("Files").classes("font-bold text-lg")
            with ui.row().classes("items-center gap-4"):
                with ui.column().classes("items-center gap-1"):
                        ui.image("icons/undo.png").classes("w-6 h-6 cursor-pointer").on("click", on_undo_click)
                        ui.label("Undo").classes("font-bold text-xs")
                with ui.column().classes("items-center gap-1"):
                    ui.image("icons/redo.png").classes("w-6 h-6 cursor-pointer").on("click", on_redo_click)
                    ui.label("Redo").classes("font-bold text-xs")
                # display of the select all button
                with ui.column().classes("items-center gap-1"):
                    ui.image("icons/select.png").classes("w-6 h-6 cursor-pointer").on("click", toggle_select_all_files)
                    ui.label("Select All").classes("font-bold text-xs")
                with ui.column().classes("items-center gap-1"):
                    ui.image("icons/settings.png").classes("w-6 h-6 cursor-pointer").on("click", on_settings_click)
                    ui.label("Settings").classes("font-bold text-xs")    

        # display of the bar (now at the top so you don't have to go down through all the files)
        with files_col:
            with ui.row().classes("items-center justify-between p-5 bg-gray-200 rounded-lg shadow-inner w-full mb-5"):
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
                    ui.image("icons/clean.png").classes("w-5 h-5 cursor-pointer").on("click", on_cleanup_click)
                    ui.label("Clean").classes("font-bold text-xs")
                with ui.column().classes("items-center gap-1"):
                    ui.image("icons/enrichment.png").classes("w-5 h-5 cursor-pointer").on("click", on_enrich_click)
                    ui.label("Enrich").classes("font-bold text-xs")

        if not files:
            ui.label("(no .bib files found)")

        # display of selection choice (using checkboxes)
        for filename in files:
            with ui.row().classes("items-center w-full gap-2"):
                checkbox = ui.checkbox(on_change=lambda e, fn=filename: toggle_file_selection(fn, e.value))
                checkbox.value = filename in selected_files

                btn_color = SELECTED_COLOR if filename == selected_file else SECONDARY_COLOR
                ui.button(filename,on_click=lambda e, fn=filename: on_file_click(fn),color=btn_color).classes("flex-1 text-left").style("text-transform: none;")

        

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
    tags_dict = json_loader.load_tags()
    load_tag_colors = getattr(json_loader, 'load_tag_colors', lambda: {})
    tag_colors = load_tag_colors() or {}

    refs_col.clear()
    with refs_col:
        with ui.row().classes("items-center justify-between w-full mb-5"):
            ui.label("References").classes("font-bold text-lg")
            with ui.row().classes("items-center gap-4"):
                with ui.column().classes("items-center gap-1"):
                    ui.image("icons/search.png").classes("w-6 h-6 cursor-pointer").on("click", on_search_click)
                    ui.label("Search").classes("font-bold text-xs")
                with ui.column().classes("items-center gap-1"):
                    ui.image("icons/tag.png").classes("w-6 h-6 cursor-pointer").on("click", on_tag_click)
                    ui.label("Tag").classes("font-bold text-xs")
                with ui.column().classes("items-center gap-1"):
                    ui.image("icons/untag.png").classes("w-6 h-6 cursor-pointer").on("click", on_untag_click)
                    ui.label("Untag").classes("font-bold text-xs")
                with ui.column().classes("items-center gap-1"):
                    ui.image("icons/sorting.png").classes("w-7 h-7 cursor-pointer").on("click", on_sort_click)
                    ui.label("Sort").classes("font-bold text-xs")
                with ui.column().classes("items-center gap-1"):
                    ui.image("icons/filter.png").classes("w-6 h-6 cursor-pointer").on("click", on_filter_click)
                    ui.label("Filter").classes("font-bold text-xs")
                with ui.column().classes("items-center gap-1"):
                    ui.image("icons/select.png").classes("w-6 h-6 cursor-pointer").on("click", lambda: toggle_select_all_references(filename))
                    ui.label("Select All").classes("font-bold text-xs")

        bib_file = files[filename]
        tags_dict = json_loader.load_tags() or {}

        if not getattr(bib_file, 'content', None):
            ui.label("(no references found)").classes("text-sm italic text-gray-600")
            return

        for ref in iter_references(bib_file):
            author = normalize_field(getattr(ref, 'author', None) or "Unknown Author")
            title = normalize_field(getattr(ref, 'title', None) or "Untitled")
            year = normalize_field(getattr(ref, 'year', None) or "N.D.")
            label = f"{author} ({year}): {title}"

            ref_tags = [tag for tag, cite_keys in tags_dict.items() if getattr(ref, 'cite_key', None) in (cite_keys or [])]
            if ref_tags:
                with ui.row().classes("ml-8 gap-1"):
                    for tag in sorted(ref_tags):
                        color = tag_colors.get(tag, "#F187D0")
                        ui.label(tag).classes("text-[10px] px-2 py-[2px] rounded-md").style(f"background-color: {color}; color: black;")

            with ui.row().classes("items-center w-full gap-2"):
                checkbox = ui.checkbox(on_change=lambda e, r=ref: toggle_reference_selection(r, e.value)).style(
                    f"accent-color: {SUCCESS_COLOR};")
                checkbox.value = getattr(ref, 'cite_key', None) in selected_references
                btn_color = SELECTED_COLOR if ref is selected_ref else SECONDARY_COLOR
                ui.button(label,on_click=lambda e, r=ref: on_ref_click(r),color=btn_color).classes("flex-1 text-left").style("text-transform: none;")

def toggle_reference_selection(ref, checked: bool):
    """
    Toggles the selection for the REFERENCES in the REFERENCES column
    """
    key = getattr(ref, 'cite_key', None)
    if not key:
        return 
    if checked:
        selected_references.add(key)
    else:
        selected_references.discard(key)


def toggle_select_all_references(filename: str):
    """
    Toggles the selection for ALL of the REFERENCES in the REFERENCES column
    """
    global selected_references, all_selected_references
    bib_file = files[filename]
    refs = iter_references(bib_file)
    if all_selected_references:
        # Deselect all
        selected_references.clear()
        all_selected_references = False
    else:
        # Select all
        selected_references = {getattr(r,'cite_key', None) for r in refs if getattr(r, 'cite_key', None)}
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
    global selected_file, selected_ref, search_active
    search_active = False
    selected_file = filename
    selected_ref = None
    selected_references.clear()
    populate_files()
    refs_col.clear()
    bib_col.clear()
    populate_refs_for_file(filename)


def on_ref_click(ref: dict):
    """
    Toggles the display of the BIB column with the bib content 
    from the reference from the file that was clicked
    """
    global selected_ref, search_active
    selected_ref = ref
    if search_active:
        populate_bib_for_ref(ref)
        show_search_results(search_results, search_term)
    else:
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


def on_sort_click():
    if not selected_file:
        ui.notify("Please select a file first", color="red")
        return

    bib_file = files[selected_file]
    references = iter_references(bib_file)

    num_selected = len(selected_references)
    total_refs = len(references)

    if 0 < num_selected < total_refs:
        ui.notify("Some references are selected, but sort will apply to all references in the file", color="orange")

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


async def on_filter_click():
    if not selected_file:
        ui.notify("Please select a file first", color="red")
        return

    bib_file = files[selected_file]

    with ui.dialog() as mode_dialog, ui.card().classes("p-4 bg-gray-100 rounded shadow w-80"):
        ui.label("Select Filter Mode").classes("font-bold text-lg mb-4")
        mode = ui.radio(
            options={"exists": "Has Field", "value": "Field Contains Value"},
            value="exists"
        )
        with ui.row().classes("justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=mode_dialog.close, color=PRIMARY_COLOR)
            ui.button("Next", on_click=lambda e: mode_dialog.submit(mode.value), color=SECONDARY_COLOR)

    selected_mode = await mode_dialog
    if selected_mode is None:
        return

    with ui.dialog() as field_dialog, ui.card().classes("p-4 bg-gray-100 rounded shadow w-80"):
        ui.label("Filter References").classes("font-bold text-lg mb-4")
        field_input = ui.input(label="Field name(e.g., author, journal, doi)").classes("w-full mb-2")
        value_input = None
        if selected_mode == "value":
            value_input = ui.input(label="Field Value").classes("w-full mb-2")

        def apply_action():
            field = (field_input.value or "").strip()
            if not field:
                ui.notify("Enter a field name", color="red")
                return
            if selected_mode == "exists":
                refs = filtering.filterByFieldExistence(bib_file, field)
                desc = f"has field '{field}'"
            else:
                value = (value_input.value or "").strip()
                if not value:
                    ui.notify("Enter a field value", color="red")
                    return
                refs = filtering.filterByFieldValue(bib_file, field, value)
                desc = f"{field} contains '{value}'"
            field_dialog.close()

            global search_active, search_results, search_term
            search_active = True
            search_results = refs
            search_term = desc
            show_search_results(refs, search_term)

        with ui.row().classes("justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=field_dialog.close, color=PRIMARY_COLOR)
            ui.button("Apply", on_click=apply_action, color=SECONDARY_COLOR)
    await field_dialog


def on_cleanup_click():
    if not selected_files:
        ui.notify("Please select at least one file to clean", color="red")
        return
    wd = json_loader.get_wd_path()
    count = 0
    for filename in list(selected_files):
        try:
            path = os.path.join(wd, filename)
            bib_file = parse_bib(path)
            cleanup.cleanup(bib_file)
            generate_bib(bib_file, path)
            files[filename] = parse_bib(path)
            count += 1
        except Exception as e:
            ui.notify(f"Cleanup failed for {filename}: {e}", color="red")
    if count:
        ui.notify(f"Cleanup done for {count} file(s)", color="green")
        reload_after_edit()

def on_tag_click():
    if not selected_file:
        ui.notify("Please select a file to tag references from", color="red")
        return
    
    bib_file = files[selected_file]
    ref_map = {r.cite_key: r for r in iter_references(bib_file)}
    selected_refs = [ref_map[k] for k in selected_references if k in ref_map]
    if not selected_refs:
        ui.notify("Please select at least one reference to tag", color="red")
        return

    load_tag_colors = getattr(json_loader, 'load_tag_colors', lambda: {})
    dump_tag_colors = getattr(json_loader, 'dump_tag_colors', lambda d: None)
    tag_colors = load_tag_colors() or {}

    with ui.dialog() as dialog, ui.card().classes("p-4 bg-gray-100 rounded shadow w-[340px]"):
        ui.label("Add Tag").classes("font-bold text-lg mb-2")
        tag_input = ui.input(label="Tag name").classes("w-full")

        with ui.row().classes("items-center gap-2"):
            color_input = ui.color_input(label="Tag Color",value="#EC86F0",on_change=lambda e: color_swatch.style(f"width:24px; height:24px; border-radius:4px; "f"background-color:{e.value}; display:inline-block; margin-left:8px;"))
            color_swatch = ui.label().style("width:24px; height:24px; border-radius:4px; background-color:#EC86F0; display:inline-block; margin-left:8px;")

        def on_color_change(_):
            color_swatch.style(f"width:24px; height:24px; border-radius:4px; background-color:{color_input.value}; display:inline-block; margin-left:8px;")

        color_input.on("input", on_color_change)
        color_input.on("change", on_color_change)

        def on_tag_change(e):
            name = (e.value or "").strip()
            if name in tag_colors:
                color_input.value = tag_colors[name]
        tag_input.on("change", on_tag_change)
        tag_input.on("input", on_tag_change)

        def apply():
            tag_name = (tag_input.value or "").strip()
            if not tag_name:
                ui.notify("Please enter a tag name", color="red")
                return

            try:
                tag_refs(tag_name, selected_refs)
            except Exception as e:
                ui.notify(f"Tagging failed: {e}", color="red")
                return

            v = (color_input.value or "").strip()
            if v:
                tag_colors[tag_name] = v
                try:
                    dump_tag_colors(tag_colors)
                except Exception as e:
                    ui.notify(f"Could not save tag color: {e}", color="orange")

            dialog.close()
            ui.notify(f"Tagged {len(selected_refs)} reference(s) as '{tag_name}'", color="green")
            populate_refs_for_file(selected_file)

        with ui.row().classes("justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close, color=PRIMARY_COLOR).style("text-transform: none;")
            ui.button("Apply", on_click=apply, color=SECONDARY_COLOR).style("text-transform: none;")
    dialog.open()

def current_file():
    if selected_file:
        return selected_file
    if len(selected_files) == 1:
        return next(iter(selected_files))
    return None 

def on_untag_click():
    file = current_file()
    if not file:
        ui.notify("Please select a file first, then select references to untag", color="red")
        return
    
    bib_file = files.get(file)
    if not bib_file:
        ui.notify("Could not load the current file", color="red")
        return
    
    tags = json_loader.load_tags() or {}
    selected_tags = list(selected_references)

    if selected_tags:
        changed = False
        for tag, cite_keys in list(tags.items()):
            initial = set(cite_keys or [])
            final = [k for k in initial if k not in selected_tags]
            if len(final) != len(initial):
                changed = True
                if final:
                    tags[tag] = final
                else:
                    tags.pop(tag, None)    
        if changed:
            json_loader.dump_tags(tags)
            ui.notify(f"Removed tags from {len(selected_references)} selected reference(s)", color="green")
            populate_refs_for_file(file)
        else:
            ui.notify("No tags found on the selected references", color="orange")
        return

    file_keys = {r.cite_key for r in iter_references(bib_file)}
    tags_in_file = sorted([t for t, keys in tags.items() if any(k in file_keys for k in (keys or []))])
    
    with ui.dialog() as dialog, ui.card().classes("p-4 bg-gray-100 rounded shadow w-[360px]"):
        ui.label("Remove tag from current file").classes("font-bold text-lg mb-2")
        tag_input = ui.input(label="Tag name").classes("w-full")
        if tags_in_file:
            ui.label("Existing tags in this file: " + ", ".join(tags_in_file)).classes("text-xs text-gray-600 mt-1")
        
        def apply():
            tag_name = (tag_input.value or "").strip()
            if not tag_name:
                ui.notify("Enter a tag name", color="red")
                return
            if tag_name not in tags:
                ui.notify(f"Tag '{tag_name}' not found", color="orange")
                dialog.close()
                return
            remaining = [k for k in tags.get(tag_name, []) if k not in file_keys]
            if remaining:
                tags[tag_name] = remaining
            else:
                tags.pop(tag_name, None)
            json_loader.dump_tags(tags)
            ui.notify(f"Removed tag '{tag_name}' from all references in {file}", color="green")
            dialog.close()
            populate_refs_for_file(file)
        
        with ui.row().classes("justify-end gap-2 mt-3"):
            ui.button("Cancel", on_click=dialog.close, color=PRIMARY_COLOR).style("text-transform: none;")
            ui.button("Remove", on_click=apply, color=SECONDARY_COLOR).style("text-transform: none;")
    
    dialog.open()


def on_undo_click():
    file = current_file()
    if not file:
        ui.notify("Please select one file first", color="red")
        return
    try: 
        wd = json_loader.get_wd_path()
        path = os.path.join(wd, selected_file)
        bib = parse_bib(path)
        undo(bib, 1)
        files[selected_file] = parse_bib(path)
        ui.notify("Undo successful", color="green")
        populate_refs_for_file(selected_file)
    except Exception as e:
        ui.notify(f"Undo failed: {e}", color="red")

def on_redo_click():
    file = current_file()
    if not file:
        ui.notify("Please select one file first", color="red")
        return
    try: 
        wd = json_loader.get_wd_path()
        path = os.path.join(wd, selected_file)
        bib = parse_bib(path)
        redo(bib, 1)
        files[selected_file] = parse_bib(path)
        ui.notify("Undo successful", color="green")
        populate_refs_for_file(selected_file)
    except Exception as e:
        ui.notify(f"Undo failed: {e}", color="red")

def show_search_results(ref_list, term=None):
    refs_col.clear()
    with refs_col:
        header = f"References (search: {term})"
        with ui.row().classes("items-center justify-between w-full mb-5"):
            ui.label(header).classes("font-bold text-lg")
        tags_dict = json_loader.load_tags() or {}
        tag_colors = json_loader.load_tag_colors() or {}
        for ref in ref_list:
            k = getattr(ref, 'cite_key', None)

            ref_tags = [t for t, keys in tags_dict.items() if k in (keys or [])]
            
            if ref_tags:
                with ui.row().classes("ml-8 gap-1 mb-1"):
                    for t in sorted(ref_tags):
                        color = tag_colors.get(t, "#E5E7EB")
                        ui.label(t).classes("text-[10px] px-2 py-[2px] rounded-md").style(
                            f"background-color: {color}; color: black;"
                        )
            author = normalize_field(getattr(ref, 'author', None) or "Unknown Author")
            title = normalize_field(getattr(ref, 'title', None) or "Untitled")
            year = normalize_field(getattr(ref, 'year', None) or "N.D.")
            label = f"{author} ({year}): {title}"
            
            btn_color = SELECTED_COLOR if ref is selected_ref else SECONDARY_COLOR
            with ui.row().classes("items-center w-full gap-2"):
                checkbox = ui.checkbox(on_change=lambda e, r=ref: toggle_reference_selection(r, e.value)).style(f"accent-color: {SUCCESS_COLOR};")
                checkbox.value = k in selected_references
                ui.button(label, on_click=lambda e, r=ref: on_ref_click(r), color=btn_color).classes("flex-1 text-left").style("text-transform: none;")


def on_search_click():
    with ui.dialog() as dialog, ui.card().classes("p-4 bg-gray-100 rounded shadow w-[380px]"):
        ui.label("Search").classes("font-bold text-lg mb-2")
        term_input = ui.input(label="Search term").classes("w-full")
        def search():
            term = (term_input.value or "").strip()
            if not term:
                ui.notify("Enter a search term", color="red")
                return
            dialog.close()

            file = current_file()
            if not file:
                ui.notify("Select one file", color="orange")
                return
            bib_file = files.get(file)
            if not bib_file:
                ui.notify("Could not load the current file", color="red")
                return
            try:
                matches = filtering.search(bib_file, term) 
                if matches == -1 or not matches:
                    ui.notify("No matches found", color="orange")
                    return
                
                global search_active, search_results, search_term
                search_active = True
                search_results = matches
                search_term = term
                show_search_results(matches, search_term)
                ui.notify(f"Found {len(matches)} match(es)", color="green")
            except Exception as e:
                ui.notify(f"Search failed: {e}", color="red")

        with ui.row().classes("justify-end gap-2 mt-3"):
            ui.button("Cancel", on_click=dialog.close, color=PRIMARY_COLOR).style("text-transform: none;")
            ui.button("Search", on_click=search, color=SECONDARY_COLOR).style("text-transform: none;")
    dialog.open()

def ref_list(refs: list):
    refs_col.clear()
    with refs_col:
        with ui.row().classes("items-center justify-between w-full mb-5"):
            ui.label(f"References with search term applied").classes("font-bold text-lg")
    if not refs:
        ui.label("(no references found)").classes("text-sm italic text-gray-600")
        return
    tags_dict = json_loader.load_tags() or {}
    tag_colors = json_loader.load_tag_colors() or {}
    for ref in refs:
        author = normalize_field(getattr(ref, 'author', None) or "Unknown Author")
        title = normalize_field(getattr(ref, 'title', None) or "Untitled")
        year = normalize_field(getattr(ref, 'year', None) or "N.D.")
        label = f"{author} ({year}): {title}"
        k = getattr(ref, 'cite_key', None)
        with ui.row().classes("items-center w-full gap-2"):
            checkbox = ui.checkbox(on_change=lambda e, r=ref: toggle_reference_selection(r, e.value)).style(f"accent-color: {SUCCESS_COLOR};")
            checkbox.value = k in selected_references
            btn_classes = "flex-1 text-left"
        
        if selected_ref and k and getattr(selected_ref, 'cite_key', None) == k:
            btn_classes += " bg-gray-300"
            ui.button(label, on_click=lambda e, r=ref: on_ref_click(r), color=SECONDARY_COLOR).classes(btn_classes).style("text-transform: none;")
            if k and tags_dict:
                ref_tags = [t for t, keys in tags_dict.items() if k in (keys or [])]
                if ref_tags:
                    with ui.row().classes("ml-8 gap-1"):
                        for t in sorted(ref_tags):
                            color = tag_colors.get(t, "#D88BD8")
                            ui.label(t).classes("text-[10px] px-2 py-[2px] rounded-md").style(f"background-color: {color}; color: black;")

def on_enrich_click():
    if not selected_files:
        ui.notify("Please select at least one file to enrich", color="red")
        return
    
    progress = ui.dialog()
    with progress, ui.card().classes("p-4 bg-white rounded shadow w-[260px] items-center"):
        ui.label("Enrichment is being done").classes("font-bold mb-2")
        ui.spinner(size="lg")
        ui.label("This can take a while.").classes("text-xs text-gray-600")
    progress.open()

    done_enrichment = threading.Event()
    result = {'count': 0, 'errors': []}

    def enrich():
        try:
            wd = json_loader.get_wd_path()
            count = 0
            errors = []
            for filename in list(selected_files):
                try:
                    path = os.path.join(wd, filename)
                    bib = parse_bib(path)
                    enrichment.sanitize_bib_file(bib)
                    generate_bib(bib, path)
                    files[filename] = parse_bib(path)
                    populate_refs_for_file(filename)
                    count += 1
                except Exception as e:
                    errors.append((filename, str(e)))
            result['count'] = count
            result['errors'] = errors
        except Exception as e:
            result['errors'] = result.get('errors', []) + [("unknown", str(e))]
        finally:
            done_enrichment.set()
    threading.Thread(target=enrich, daemon=True).start()  

    def done():
        if not done_enrichment.is_set():
            return
        try:
            for fn, err in result.get('errors', []):
                if fn == "unknown":
                    ui.notify(f"Enrichment failed: {err}", color="red")
                else:
                    ui.notify(f"Enrichment failed for {fn}: {err}", color="red")
            if result.get('count', 0):
                ui.notify(f"Enrichment was successful for {result['count']} file(s)", color="green")
            reload_after_edit()
        finally:
            try:
                progress.close()
            except Exception:
                pass
            done_enrichment.clear()

    ui.timer(0.2, done)


def order_by_field(file: BibFile, field: str, descending=False):
    references = [ref for ref in getattr(file,'content', []) if is_reference(ref)]

    def get_field_safe(ref, field):
        value = getattr(ref, field, None)
        return value if value is not None else ""

    sorted_refs = sorted(references, key=lambda ref: get_field_safe(ref, field), reverse=descending)
    remaining_entries = [e for e in getattr(file,'content',[]) if not is_reference(e)]
    file.content = remaining_entries + sorted_refs


def save_bib_file(filename: str, bib_file):
    wd = json_loader.get_wd_path()
    path = os.path.join(wd, filename)
    try:
        generate_bib(bib_file, path)
        files[filename] = parse_bib(path)
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
            new_refs = iter_references(files[selected_file])
            matched_ref = next((r for r in new_refs if r.cite_key == selected_ref.cite_key), None)
            if matched_ref:
                selected_ref = matched_ref
                populate_bib_for_ref(selected_ref)
            else:
                selected_ref = None


def open_abbreviations_json():
    file_path = os.path.abspath("jsons/abbreviations.json")

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

def open_synonyms_json():
    file_path = os.path.abspath("jsons/synonyms.json")

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
        ui.notify("synonyms.json is being opened", color="green")
    except Exception as e:
        ui.notify(f"Could not open file: {e}", color="red")


def save_settings(directory_input, abs_strong_match_input, abs_strong_mismatch_input, remove_newlines_checkbox,
                    convert_unicode_checkbox, prefer_doi_checkbox,
                    keep_comments_checkbox, keep_comment_entries_checkbox, lowercase_entry_types_checkbox,
                    lowercase_fields_checkbox, braces_checkbox, quotes_checkbox,):
    path = directory_input.value.strip()
    if not path:
        ui.notify("Please enter a valid path.", color="red")
        return

    os.makedirs(path, exist_ok=True)

    cfg = json_loader.load_config() or {}

    def parse_float(value, default):
        try:
            v = float(value)
            return v
        except Exception:
            return default
        
    abs_strong_match = parse_float(abs_strong_match_input.value, cfg.get("abstract_strong_match", 0.9))
    abs_strong_mismatch = parse_float(abs_strong_mismatch_input.value, cfg.get("abstract_strong_mismatch", 0.5))
    abs_strong_match = max(0.0, min(1.0, abs_strong_match))
    abs_strong_mismatch = max(0.0, min(1.0, abs_strong_mismatch))

    cfg["working_directory"] = path
    cfg["abstract_strong_match"] = abs_strong_match
    cfg["abstract_strong_mismatch"] = abs_strong_mismatch
    cfg["remove_newlines_in_fields"] = bool(remove_newlines_checkbox.value)
    cfg["convert_special_symbols_to_unicode"] = bool(convert_unicode_checkbox.value)
    cfg["prefer_doi_over_url"] = bool(prefer_doi_checkbox.value)
    cfg["keep_comments"] = bool(keep_comments_checkbox.value)
    cfg["keep_comment_entries"] = bool(keep_comment_entries_checkbox.value)
    cfg["lowercase_entry_types"] = bool(lowercase_entry_types_checkbox.value)
    cfg["lowercase_fields"] = bool(lowercase_fields_checkbox.value)
    cfg["change_enclosures_to_braces"] = bool(braces_checkbox.value)
    cfg["change_enclosures_to_quotation_marks"] = bool(quotes_checkbox.value)
    cfg["working_directory"] = path

    json_loader.dump_config(cfg)

    ui.notify(f"Configuration saved! Directory: {path}", color="green")
    ui.timer(1.5, lambda: ui.run_javascript('window.location.href = "/"'))


@ui.page("/setup")
def setup_page():
    cfg = json_loader.load_config()
    with ui.column().classes("items-center w-full"):
        ui.label("Setup").classes("text-4xl font-bold mb-4 mt-6 self-start ml-[400px]").style(
            f"color: {SUCCESS_COLOR};")

        with ui.column().classes("w-[700px] mx-auto p-6 bg-gray-100 rounded-2xl shadow-lg"):
            ui.label("Synonyms").classes("font-bold text-lg mb-1 border-b-2 pb-1 w-full").style(f"border-color: {SECONDARY_COLOR};")
            with ui.row().classes("justify-start items-start w-full mb-6 mt-3 gap-10"):
                with ui.row().classes("items-center gap-2 ml-6"):
                    ui.image("icons/customize_rules.png").classes("w-7 h-7")
                    ui.button("Customize Synonyms", color=SECONDARY_COLOR, on_click=open_synonyms_json).classes("text-xs px-3 py-1 rounded-md").style("text-transform: none;")
                    
            ui.label("Abbreviations").classes("font-bold text-lg mb-1 border-b-2 pb-1 w-full").style(f"border-color: {SECONDARY_COLOR};")
            with ui.row().classes("justify-start items-start w-full mb-6 mt-3 gap-10"):
                with ui.row().classes("items-center gap-2 ml-6"):
                    ui.image("icons/customize_rules.png").classes("w-7 h-7")
                    ui.button("Customize Abbreviations", color=SECONDARY_COLOR, on_click=open_abbreviations_json).classes("text-xs px-3 py-1 rounded-md").style("text-transform: none;")

            ui.label("Merge thresholds").classes("font-bold text-lg mb-1 border-b-2 pb-1 w-full").style(f"border-color: {SECONDARY_COLOR};")
            with ui.row().classes("gap-4 mt-3 ml-2"):
                abs_strong_match_input = ui.input(label="Abstract strong match threshold (0.0 - 1.0)", value=str(cfg.get("abstract_strong_match", 0.9)),).props('type=number step=0.01 min=0 max=1').classes("w-[320px]")
                abs_strong_mismatch_input = ui.input(label="Abstract strong mismatch threshold (0.0 - 1.0)", value=str(cfg.get("abstract_strong_mismatch", 0.5)),).props('type=number step=0.01 min=0 max=1').classes("w-[320px]")

            ui.label("Merge and parsing options").classes("font-bold text-lg mb-1 border-b-2 pb-1 w-full mt-4").style(f"border-color: {SECONDARY_COLOR};")
            with ui.column().classes("gap-2 mt-3 ml-2"):
                remove_newlines_checkbox = ui.checkbox("Remove newlines in fields")
                remove_newlines_checkbox.value = bool(cfg.get("remove_newlines_in_fields", False))

                convert_unicode_checkbox = ui.checkbox("Convert special symbols to Unicode")
                convert_unicode_checkbox.value = bool(cfg.get("convert_special_symbols_to_unicode", False))

                prefer_doi_checkbox = ui.checkbox("Prefer DOI when merging conflicts")
                prefer_doi_checkbox.value = bool(cfg.get("prefer_doi_over_url", False))

                keep_comments_checkbox = ui.checkbox("Keep inline comments in .bib")
                keep_comments_checkbox.value = bool(cfg.get("keep_comments", False))

                keep_comment_entries_checkbox = ui.checkbox("Keep @comment entries")
                keep_comment_entries_checkbox.value = bool(cfg.get("keep_comment_entries", False))

                lowercase_entry_types_checkbox = ui.checkbox("Lowercase entry types (e.g., @article)")
                lowercase_entry_types_checkbox.value = bool(cfg.get("lowercase_entry_types", False))

                lowercase_fields_checkbox = ui.checkbox("Lowercase field names (e.g., title, author)")
                lowercase_fields_checkbox.value = bool(cfg.get("lowercase_fields", False))

                braces_checkbox = ui.checkbox("Change enclosures to braces {...}")
                braces_checkbox.value = bool(cfg.get("change_enclosures_to_braces", False))

                quotes_checkbox = ui.checkbox('Change enclosures to quotation marks "..."')
                quotes_checkbox.value = bool(cfg.get("change_enclosures_to_quotation_marks", False))

            ui.separator().classes("my-6")
            ui.label("Working Directory").classes("font-bold text-lg mb-2")
            directory_input = ui.input(label="Path to the working directory").classes("w-full")
            directory_input.value = cfg.get("working_directory", "")

        with ui.row().classes("justify-end mt-6"):
            ui.button("Save", color=SUCCESS_COLOR, on_click=lambda: save_settings(
                directory_input, abs_strong_match_input, abs_strong_mismatch_input, remove_newlines_checkbox,
                convert_unicode_checkbox, prefer_doi_checkbox, keep_comments_checkbox,
                keep_comment_entries_checkbox, lowercase_entry_types_checkbox, lowercase_fields_checkbox,
                braces_checkbox, quotes_checkbox,
            ),).classes("px-6 py-2 rounded-lg font-semibold").style("text-transform: none;")


@ui.page('/')
def main_page():
    global files_col, refs_col, bib_col, merge
    global selected_file, selected_ref
    selected_file = None
    selected_ref = None
    
    cfg = json_loader.load_config()
    wd = (cfg or {}).get("working_directory") or ""
    if not wd:
        global files, selected_files, all_selected_files, selected_references, all_selected_references
        files = {}
        selected_file = None
        selected_ref = None
        selected_files = set()
        all_selected_files = False
        selected_references = set()
        all_selected_references = False
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
    interface_handler.user_interface = "GUI"
    interface_handler.set_merge_object(merge)

def on_settings_click():
    ui.run_javascript('window.location.href = "/settings"')

@ui.page("/settings")
def setup_page():
    cfg = json_loader.load_config()
    with ui.column().classes("items-center w-full"):
        ui.label("Settings").classes("text-4xl font-bold mb-4 mt-6 self-start ml-[400px]").style(
            f"color: {SUCCESS_COLOR};")

        with ui.column().classes("w-[700px] mx-auto p-6 bg-gray-100 rounded-2xl shadow-lg"):
            ui.label("Synonyms").classes("font-bold text-lg mb-1 border-b-2 pb-1 w-full").style(f"border-color: {SECONDARY_COLOR};")
            with ui.row().classes("justify-start items-start w-full mb-6 mt-3 gap-10"):
                with ui.row().classes("items-center gap-2 ml-6"):
                    ui.image("icons/customize_rules.png").classes("w-7 h-7")
                    ui.button("Customize Synonyms", color=SECONDARY_COLOR, on_click=open_synonyms_json).classes("text-xs px-3 py-1 rounded-md").style("text-transform: none;")
                    
            ui.label("Abbreviations").classes("font-bold text-lg mb-1 border-b-2 pb-1 w-full").style(f"border-color: {SECONDARY_COLOR};")
            with ui.row().classes("justify-start items-start w-full mb-6 mt-3 gap-10"):
                with ui.row().classes("items-center gap-2 ml-6"):
                    ui.image("icons/customize_rules.png").classes("w-7 h-7")
                    ui.button("Customize Abbreviations", color=SECONDARY_COLOR, on_click=open_abbreviations_json).classes("text-xs px-3 py-1 rounded-md").style("text-transform: none;")
                    
            ui.label("Merge thresholds").classes("font-bold text-lg mb-1 border-b-2 pb-1 w-full").style(f"border-color: {SECONDARY_COLOR};")
            with ui.row().classes("gap-4 mt-3 ml-2"):
                abs_strong_match_input = ui.input(label="Abstract strong match threshold (0.0 - 1.0)", value=str(cfg.get("abstract_strong_match", 0.9)),).props('type=number step=0.01 min=0 max=1').classes("w-[320px]")
                abs_strong_mismatch_input = ui.input(label="Abstract strong mismatch threshold (0.0 - 1.0)", value=str(cfg.get("abstract_strong_mismatch", 0.5)),).props('type=number step=0.01 min=0 max=1').classes("w-[320px]")

            ui.label("Merge and parsing options").classes("font-bold text-lg mb-1 border-b-2 pb-1 w-full mt-4").style(f"border-color: {SECONDARY_COLOR};")
            with ui.column().classes("gap-2 mt-3 ml-2"):
                remove_newlines_checkbox = ui.checkbox("Remove newlines in fields")
                remove_newlines_checkbox.value = bool(cfg.get("remove_newlines_in_fields", False))

                convert_unicode_checkbox = ui.checkbox("Convert special symbols to Unicode")
                convert_unicode_checkbox.value = bool(cfg.get("convert_special_symbols_to_unicode", False))

                prefer_doi_checkbox = ui.checkbox("Prefer DOI when merging conflicts")
                prefer_doi_checkbox.value = bool(cfg.get("prefer_doi_over_url", False))

                keep_comments_checkbox = ui.checkbox("Keep inline comments in .bib")
                keep_comments_checkbox.value = bool(cfg.get("keep_comments", False))

                keep_comment_entries_checkbox = ui.checkbox("Keep @comment entries")
                keep_comment_entries_checkbox.value = bool(cfg.get("keep_comment_entries", False))

                lowercase_entry_types_checkbox = ui.checkbox("Lowercase entry types (e.g., @article)")
                lowercase_entry_types_checkbox.value = bool(cfg.get("lowercase_entry_types", False))

                lowercase_fields_checkbox = ui.checkbox("Lowercase field names (e.g., title, author)")
                lowercase_fields_checkbox.value = bool(cfg.get("lowercase_fields", False))

                braces_checkbox = ui.checkbox("Change enclosures to braces {...}")
                braces_checkbox.value = bool(cfg.get("change_enclosures_to_braces", False))

                quotes_checkbox = ui.checkbox('Change enclosures to quotation marks "..."')
                quotes_checkbox.value = bool(cfg.get("change_enclosures_to_quotation_marks", False))

            ui.separator().classes("my-6")
            ui.label("Working Directory").classes("font-bold text-lg mb-2")
            directory_input = ui.input(label="Path to the working directory").classes("w-full")
            directory_input.value = cfg.get("working_directory", "")

        with ui.row().classes("justify-end mt-6"):
            ui.button("Save", color=SUCCESS_COLOR, on_click=lambda: save_settings(
                directory_input, abs_strong_match_input, abs_strong_mismatch_input, remove_newlines_checkbox,
                convert_unicode_checkbox, prefer_doi_checkbox, keep_comments_checkbox,
                keep_comment_entries_checkbox, lowercase_entry_types_checkbox, lowercase_fields_checkbox,
                braces_checkbox, quotes_checkbox,
            ),).classes("px-6 py-2 rounded-lg font-semibold").style("text-transform: none;")

@app.on_connect
async def on_connect(client):
    await ui.context.client.connected()
    global connected_users
    connected_users += 1
    print(f'Client connected. Total: {connected_users}')


@app.on_disconnect
async def on_disconnect(client):
    global connected_users
    connected_users -= 1
    print(f'Client disconnected. Total: {connected_users}')
    await asyncio.sleep(1)
    if connected_users == 0:
        print('There are no active browser windows so the gui will close')
        app.shutdown()
        os._exit(0)


def start_gui():
    ui.run()


if __name__ in {"__main__", "__mp_main__"}:
    start_gui()
