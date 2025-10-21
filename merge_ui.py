import builtins
import threading
import queue
from collections import deque
from nicegui import ui

PRIMARY_COLOR = "#CCE0D4"
SECONDARY_COLOR = "#9AC1A9"


class Merge:
    def __init__(self, on_done, on_error=None):
        self.on_done = on_done
        self.on_error = on_error or (lambda msg: ui.notify(msg, color='red'))
        self._prompt_dialog = None
        self._progress_dialog = None
        self._initialized = False
        self._print_buf = deque(maxlen=200)
        self._prompt_q: "queue.Queue[dict]" = queue.Queue()
        self._current_prompt = None
        self._done_event = threading.Event()
        self._result = None
        self._error = None
        self._selected_files_list = None
        self._files_map = None
        self._merge_files_fn = None
        self._orig_input = builtins.input
        self._orig_print = builtins.print

    def init_ui(self):
        if self._initialized:
            return
        self._prompt_dialog = ui.dialog()
        self._progress_dialog = ui.dialog()
        ui.timer(0.2, self._tick_prompts)
        ui.timer(0.2, self._tick_done)
        self._initialized = True

    def start(self, selected_files_list, files_map, merge_files_fn):
        self._selected_files_list = list(selected_files_list)
        self._files_map = files_map
        self._merge_files_fn = merge_files_fn
        self._done_event.clear()
        self._result = None
        self._error = None
        self._print_buf.clear()
        with self._prompt_q.mutex:
            self._prompt_q.queue.clear()
        self._current_prompt = None
        self._show_progress()
        t = threading.Thread(target=self._worker, daemon=True)
        t.start()

    def print_hook(self, *args, **kwargs):
        try:
            self._orig_print(*args, **kwargs)
        except Exception:
            pass
        try:
            text = ' '.join(str(a) for a in args)
            self._print_buf.append(text)
        except Exception:
            pass

    def _make_prompt(self, kind, prompt_text):
        return {
            'kind': kind,
            'text': prompt_text,
            'ctx': list(self._print_buf)[-16:],
            'event': threading.Event(),
            'response': None,
        }

    def input_hook(self, prompt_text=''):
        pt = (prompt_text or '').strip()
        ctx_joined = '\n'.join(list(self._print_buf)[-20:])

        if 'Choose which to keep (1 or 2)' in pt:
            req = self._make_prompt('field_conflict', pt)
        elif pt.startswith('Enter your choice (1 or 2):'):
            if 'Choose where to merge or skip:' in ctx_joined or 'References seem to be similar' in ctx_joined:
                req = self._make_prompt('dup_choice', pt)
            else:
                req = self._make_prompt('abbr_choice', pt)
        elif pt.startswith('Now input the new abbreviation for'):
            req = self._make_prompt('abbr_rename', pt)
        else:
            req = self._make_prompt('generic', pt)

        self._prompt_q.put(req)
        req['event'].wait()
        return req['response']

    def _worker(self):
        try:
            merged = self._files_map[self._selected_files_list[0]]
            for fn in self._selected_files_list[1:]:
                merged = self._merge_files_fn(merged, self._files_map[fn])
            self._result = merged
            self._error = None
        except Exception as e:
            self._result = None
            self._error = str(e)
        finally:
            self._done_event.set()

    def _tick_prompts(self):
        if self._current_prompt is not None:
            return
        try:
            req = self._prompt_q.get_nowait()
        except queue.Empty:
            return
        self._current_prompt = req
        self._show_prompt(req)

    def _tick_done(self):
        if not self._done_event.is_set():
            return
        self._done_event.clear()
        self._hide_progress()
        if self._error:
            self.on_error(f'Merge failed: {self._error}')
            return
        self.on_done(self._result, self._selected_files_list)

    def _show_progress(self):
        self._progress_dialog.clear()
        with self._progress_dialog, ui.card().classes('p-4 bg-gray-100 rounded shadow w-[360px]'):
            ui.label('Merging...').classes('font-bold text-lg mb-2')
            ui.spinner(size='lg')
            ui.label('Resolve prompts as they appear.').classes('text-sm mt-2')
        self._progress_dialog.open()

    def _hide_progress(self):
        try:
            self._progress_dialog.close()
        except Exception:
            pass

    def _show_prompt(self, req):
        def full_code_block(text):
            return ui.code(text or '(empty)', language='text') \
                .classes('text-sm w-full whitespace-pre-wrap break-words bg-white p-2 rounded border') \
                .style('max-width: 100%;')

        def close_with(value):
            req['response'] = value
            req['event'].set()
            try:
                self._prompt_dialog.close()
            finally:
                self._current_prompt = None

        ctx = req['ctx']
        kind = req['kind']

        self._prompt_dialog.clear()
        with self._prompt_dialog, ui.card().classes('p-4 bg-gray-100 rounded shadow w-[1200px]'):
            if kind == 'field_conflict':
                header = next((l for l in reversed(ctx) if l.startswith('Conflict in field')), 'Resolve conflict')
                opt1 = next((l for l in reversed(ctx) if l.strip().startswith('1.')), '1. Option 1')
                opt2 = next((l for l in reversed(ctx) if l.strip().startswith('2.')), '2. Option 2')

                ui.label(header).classes('font-bold text-lg mb-3')
                with ui.row().classes('gap-4 w-full items-stretch'):
                    with ui.column().classes('flex-1 min-w-0'):
                        ui.label('Value from reference 1').classes('font-semibold mb-1')
                        full_code_block(opt1)
                    with ui.column().classes('flex-1 min-w-0'):
                        ui.label('Value from reference 2').classes('font-semibold mb-1')
                        full_code_block(opt2)
                with ui.row().classes('justify-end gap-2 mt-4'):
                    ui.button('Keep 1', on_click=lambda: close_with('1'), color=SECONDARY_COLOR).classes(
                        'q-btn--no-uppercase')
                    ui.button('Keep 2', on_click=lambda: close_with('2'), color=SECONDARY_COLOR).classes(
                        'q-btn--no-uppercase')

            elif kind == 'dup_choice':
                ref1 = next((l for l in reversed(ctx) if 'Reference 1 (from first file):' in l), None)
                ref2 = next((l for l in reversed(ctx) if 'Reference 2 (from second file):' in l), None)

                def strip_label(txt, label):
                    if not txt:
                        return None
                    idx = txt.find(label)
                    return txt[idx + len(label):].strip() if idx >= 0 else txt

                body1 = strip_label(ref1 or '', 'Reference 1 (from first file):')
                body2 = strip_label(ref2 or '', 'Reference 2 (from second file):')

                ui.label('Possible duplicate references').classes('font-bold text-lg mb-3')
                with ui.row().classes('gap-4 w-full items-stretch'):
                    with ui.column().classes('flex-1 min-w-0'):
                        ui.label('Reference 1').classes('font-semibold mb-1')
                        full_code_block(body1)
                    with ui.column().classes('flex-1 min-w-0'):
                        ui.label('Reference 2').classes('font-semibold mb-1')
                        full_code_block(body2)
                with ui.row().classes('justify-end gap-2 mt-4'):
                    ui.button('Merge references', on_click=lambda: close_with('1'), color=SECONDARY_COLOR).classes(
                        'q-btn--no-uppercase')
                    ui.button('Keep both', on_click=lambda: close_with('2'), color=PRIMARY_COLOR).classes(
                        'q-btn--no-uppercase')

            elif kind == 'abbr_choice':
                title = next((l for l in reversed(ctx) if l.startswith('Conflict with string abbreviation')),
                             'Abbreviation conflict')
                opt1 = next((l for l in reversed(ctx) if l.strip().startswith('1:')), '1: Option 1')
                opt2 = next((l for l in reversed(ctx) if l.strip().startswith('2:')), '2: Option 2')
                ui.label(title).classes('font-bold text-lg mb-3')
                with ui.row().classes('gap-4 w-full items-stretch'):
                    with ui.column().classes('flex-1 min-w-0'):
                        ui.label('Option 1').classes('font-semibold mb-1')
                        full_code_block(opt1)
                    with ui.column().classes('flex-1 min-w-0'):
                        ui.label('Option 2').classes('font-semibold mb-1')
                        full_code_block(opt2)
                with ui.row().classes('justify-end gap-2 mt-4'):
                    ui.button('Choose 1', on_click=lambda: close_with('1'), color=SECONDARY_COLOR).classes(
                        'q-btn--no-uppercase')
                    ui.button('Choose 2', on_click=lambda: close_with('2'), color=SECONDARY_COLOR).classes(
                        'q-btn--no-uppercase')

            elif kind == 'abbr_rename':
                ui.label('Rename abbreviation').classes('font-bold text-lg mb-3')
                ui.label(req['text']).classes('text-sm')
                new_abbr = ui.input(label='New abbreviation').classes('w-full mt-2')
                with ui.row().classes('justify-end gap-2 mt-4'):
                    ui.button('Cancel', on_click=lambda: close_with(''), color=SECONDARY_COLOR).classes(
                        'q-btn--no-uppercase')
                    ui.button('Confirm', on_click=lambda: close_with(new_abbr.value or ''),
                              color=SECONDARY_COLOR).classes('q-btn--no-uppercase')

            else:
                ui.label('Input required').classes('font-bold text-lg mb-3')
                ui.label(req['text']).classes('text-sm')
                val = ui.input(label='Value').classes('w-full mt-2')
                with ui.row().classes('justify-end gap-2 mt-4'):
                    ui.button('OK', on_click=lambda: close_with(val.value or ''), color=SECONDARY_COLOR).classes(
                        'q-btn--no-uppercase')

        self._prompt_dialog.open()
