import os
from collections import Counter
from datetime import datetime

from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.metrics import dp

from kivymd.uix.dialog import (
    MDDialog, MDDialogHeadlineText,
    MDDialogContentContainer, MDDialogButtonContainer,
)
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.list import (
    MDListItem, MDListItemLeadingIcon,
    MDListItemSupportingText, MDListItemHeadlineText,
)
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.boxlayout import MDBoxLayout

from src.services.os_utils import open_pdf_file, open_file_location, get_pdf_thumbnail


class HistoryMixin:

    # ── State Initialisation ────────────────────────────────────

    def _init_filter_state(self):
        if not hasattr(self, "_filter_excluded_courses"):
            self._filter_excluded_courses = set()
        if not hasattr(self, "_filter_excluded_schedules"):
            self._filter_excluded_schedules = set()
        if not hasattr(self, "_filter_date_from"):
            self._filter_date_from = None
        if not hasattr(self, "_filter_date_to"):
            self._filter_date_to = None
        if not hasattr(self, "_group_by_mode"):
            self._group_by_mode = None
        if not hasattr(self, "_active_folder_name"):
            self._active_folder_name = None
        if not hasattr(self, "_filter_dialog"):
            self._filter_dialog = None
        if not hasattr(self, "_course_filter_dialog"):
            self._course_filter_dialog = None
        if not hasattr(self, "_program_filter_dialog"):
            self._program_filter_dialog = None
        if not hasattr(self, "_course_checkboxes"):
            self._course_checkboxes = {}
        if not hasattr(self, "_program_checkboxes"):
            self._program_checkboxes = {}

    def _reset_all_filter_state(self):
        self._filter_excluded_courses = set()
        self._filter_excluded_schedules = set()
        self._filter_date_from = None
        self._filter_date_to = None
        self._group_by_mode = None
        self._active_folder_name = None

    # ── Screen Navigation ───────────────────────────────────────

    def open_history_screen(self):
        self._init_filter_state()

        sm = self.root.ids.screen_manager

        history_screen = sm.get_screen("HistoryScreen")
        btn = history_screen.ids.view_toggle_btn
        btn.icon = "view-list" if self.history_view_mode == "grid" else "view-grid"
        history_screen.ids.search_field.text = ""

        self._reset_all_filter_state()
        self._update_filter_badge()

        self.load_history_to_ui()

        gb = self.root.ids.global_app_bar
        gb.height = 0
        gb.size_hint_y = 0
        gb.opacity = 0
        gb.disabled = True

        nb = self.root.ids.nav_bar
        nb.height = 0
        nb.size_hint_y = 0
        nb.opacity = 0
        nb.disabled = True

        self.toggle_fab(False)

        Clock.schedule_once(lambda dt: setattr(sm, "current", "HistoryScreen"), 0)

    def go_back_from_history(self):
        if self._active_folder_name is not None:
            self._active_folder_name = None
            self._reload_current_view()
            return

        sm = self.root.ids.screen_manager
        current_screen = sm.get_screen(sm.current)
        current_screen.opacity = 0

        gb = self.root.ids.global_app_bar
        gb.size_hint_y = None
        gb.height = "64dp"
        gb.opacity = 1
        gb.disabled = False

        nb = self.root.ids.nav_bar
        nb.size_hint_y = None
        nb.height = "80dp"
        nb.opacity = 1
        nb.disabled = False

        self.toggle_fab(False)

        Clock.schedule_once(lambda dt: setattr(sm, "current", "Create PDFs"), 0)

    def toggle_history_view(self):
        self.history_view_mode = "grid" if self.history_view_mode == "list" else "list"
        self.save_setting("history_view_mode", self.history_view_mode)

        history_screen = self.root.ids.screen_manager.get_screen(
            "HistoryScreen")

        btn = history_screen.ids.view_toggle_btn
        btn.icon = "view-list" if self.history_view_mode == "grid" else "view-grid"

        history_screen.ids.rv.refresh_from_layout()

        current_text = history_screen.ids.search_field.text
        self.load_history_to_ui(search_query=current_text)

    # ── Utility ─────────────────────────────────────────────────

    def get_pdf_thumbnail(self, pdf_path):
        return get_pdf_thumbnail(pdf_path, self.thumbnail_dir)

    def open_pdf_file(self, filepath):
        open_pdf_file(filepath)

    def show_missing_file_dialog(self, filepath):
        self.missing_filepath = filepath

        cancel_btn = MDButton(style="text")
        cancel_btn.add_widget(MDButtonText(
            text=self._("Cancel"), theme_text_color="Error"))
        cancel_btn.bind(on_release=lambda x: self.missing_dialog.dismiss())

        delete_btn = MDButton(style="text")
        delete_btn.add_widget(MDButtonText(
            text=self._("Remove"), theme_text_color="Custom", text_color=[1, 0, 0, 1]))
        delete_btn.bind(on_release=self.delete_missing_record_action)

        self.missing_dialog = MDDialog(
            MDDialogHeadlineText(text=self._("File Not Found")),
            MDDialogContentContainer(
                MDLabel(
                    text=self._(
                        "This PDF has been moved or deleted. Would you like to remove it from history?")
                ),
                orientation="vertical"
            ),
            MDDialogButtonContainer(
                Widget(), cancel_btn, delete_btn, spacing="8dp"),
        )
        self.missing_dialog.open()

    def delete_missing_record_action(self, *args):
        if hasattr(self, "missing_filepath"):
            self.db.delete_record(self.missing_filepath)
            self._reload_current_view()
            self.show_snackbar(self._("Record removed successfully!"))

        if hasattr(self, "missing_dialog"):
            self.missing_dialog.dismiss()

    # ── Filter Dialog (replaces MDDropdownMenu) ─────────────────

    def show_filter_dialog(self):
        self._init_filter_state()

        if self._filter_dialog:
            self._filter_dialog.dismiss()
            self._filter_dialog = None

        content = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
        )

        items = [
            ("book-outline", self._("Filter by Course"), "filter_course"),
            ("calendar-range", self._("Filter by Date"), "filter_date"),
            ("school-outline", self._("Filter by Program"), "filter_program"),
            ("folder-outline", self._("Group by Course"), "group_course"),
            ("folder-multiple-outline", self._("Group by Program"), "group_program"),
        ]

        for icon, text, action in items:
            item = MDListItem(
                MDListItemLeadingIcon(icon=icon),
                MDListItemHeadlineText(text=text),
                on_release=lambda x, a=action: self._on_filter_action(a),
            )
            content.add_widget(item)

        active_count = self._get_active_filter_count()
        if active_count > 0:
            clear_item = MDListItem(
                MDListItemLeadingIcon(icon="filter-remove-outline"),
                MDListItemHeadlineText(text=self._("Clear Filters")),
                on_release=lambda x: self._on_filter_action("clear"),
            )
            content.add_widget(clear_item)

        close_btn = MDButton(style="text")
        close_btn.add_widget(MDButtonText(text=self._("Cancel")))
        close_btn.bind(on_release=lambda x: self._filter_dialog.dismiss())

        self._filter_dialog = MDDialog(
            MDDialogHeadlineText(text=self._("Filters & Grouping")),
            MDDialogContentContainer(
                content,
                orientation="vertical",
            ),
            MDDialogButtonContainer(
                Widget(), close_btn, spacing="8dp"),
        )
        self._filter_dialog.open()

    def _on_filter_action(self, action):
        if self._filter_dialog:
            self._filter_dialog.dismiss()
            self._filter_dialog = None

        if action == "filter_course":
            Clock.schedule_once(lambda dt: self.show_course_filter_dialog(), 0.1)
        elif action == "filter_date":
            Clock.schedule_once(lambda dt: self._show_date_from_picker(), 0.1)
        elif action == "filter_program":
            Clock.schedule_once(lambda dt: self.show_program_filter_dialog(), 0.1)
        elif action == "group_course":
            self._toggle_group_by("course")
        elif action == "group_program":
            self._toggle_group_by("program")
        elif action == "clear":
            self.clear_all_filters()

    # ── Group By ────────────────────────────────────────────────

    def _toggle_group_by(self, mode):
        if self._group_by_mode == mode:
            self._group_by_mode = None
            self._active_folder_name = None
        else:
            self._group_by_mode = mode
            self._active_folder_name = None

        self._update_filter_badge()
        self._reload_current_view()

    def open_folder_group(self, folder_name, folder_type):
        self._active_folder_name = folder_name
        self._reload_current_view()

    # ── Course Filter Dialog ────────────────────────────────────

    def show_course_filter_dialog(self):
        all_courses = self.db.get_distinct_courses()

        if not all_courses:
            self.show_snackbar(self._("No courses found in history."))
            return

        self._course_checkboxes = {}

        content = self._build_checkbox_list(
            all_courses,
            self._filter_excluded_courses,
            self._course_checkboxes,
        )

        cancel_btn = MDButton(style="text")
        cancel_btn.add_widget(MDButtonText(text=self._("Cancel")))
        cancel_btn.bind(on_release=lambda x: self._course_filter_dialog.dismiss())

        apply_btn = MDButton(style="text")
        apply_btn.add_widget(MDButtonText(text=self._("Apply")))
        apply_btn.bind(on_release=lambda x: self._apply_checkbox_filter(
            self._course_checkboxes,
            "_filter_excluded_courses",
            self._course_filter_dialog,
        ))

        self._course_filter_dialog = MDDialog(
            MDDialogHeadlineText(text=self._("Select Courses")),
            MDDialogContentContainer(
                content,
                orientation="vertical",
            ),
            MDDialogButtonContainer(
                Widget(), cancel_btn, apply_btn, spacing="8dp"),
        )
        self._course_filter_dialog.open()

    # ── Program (Schedule) Filter Dialog ────────────────────────

    def show_program_filter_dialog(self):
        all_schedules = self.db.get_distinct_schedules()

        if not all_schedules:
            self.show_snackbar(self._("No programs found in history."))
            return

        self._program_checkboxes = {}

        content = self._build_checkbox_list(
            all_schedules,
            self._filter_excluded_schedules,
            self._program_checkboxes,
        )

        cancel_btn = MDButton(style="text")
        cancel_btn.add_widget(MDButtonText(text=self._("Cancel")))
        cancel_btn.bind(on_release=lambda x: self._program_filter_dialog.dismiss())

        apply_btn = MDButton(style="text")
        apply_btn.add_widget(MDButtonText(text=self._("Apply")))
        apply_btn.bind(on_release=lambda x: self._apply_checkbox_filter(
            self._program_checkboxes,
            "_filter_excluded_schedules",
            self._program_filter_dialog,
        ))

        self._program_filter_dialog = MDDialog(
            MDDialogHeadlineText(text=self._("Select Programs")),
            MDDialogContentContainer(
                content,
                orientation="vertical",
            ),
            MDDialogButtonContainer(
                Widget(), cancel_btn, apply_btn, spacing="8dp"),
        )
        self._program_filter_dialog.open()

    # ── Shared Checkbox Dialog Builder ──────────────────────────

    def _build_checkbox_list(self, items, excluded_set, checkbox_dict):
        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(4),
            adaptive_height=True,
            padding=[dp(0), dp(8), dp(0), dp(0)],
        )

        select_all_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            padding=[dp(16), 0, dp(16), 0],
            spacing=dp(12),
        )

        all_active = len(excluded_set) == 0

        select_all_cb = MDCheckbox(
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            pos_hint={"center_y": 0.5},
            active=all_active,
        )
        select_all_label = MDLabel(
            text=self._("Select All"),
            theme_font_size="Custom",
            font_size="16sp",
            bold=True,
            pos_hint={"center_y": 0.5},
            adaptive_height=True,
        )
        select_all_row.add_widget(select_all_cb)
        select_all_row.add_widget(select_all_label)
        content.add_widget(select_all_row)

        divider = Widget(size_hint_y=None, height=dp(1))
        content.add_widget(divider)

        from kivy.uix.scrollview import ScrollView  # Cross-platform, safe

        scroll = ScrollView(
            size_hint_y=None,
            height=min(len(items) * dp(48), dp(300)),
        )
        items_list = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            spacing=dp(2),
        )

        for name in items:
            row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(48),
                padding=[dp(16), 0, dp(16), 0],
                spacing=dp(12),
            )

            is_active = name not in excluded_set

            cb = MDCheckbox(
                size_hint=(None, None),
                size=(dp(24), dp(24)),
                pos_hint={"center_y": 0.5},
                active=is_active,
            )
            label = MDLabel(
                text=name,
                theme_font_size="Custom",
                font_size="15sp",
                pos_hint={"center_y": 0.5},
                adaptive_height=True,
            )

            checkbox_dict[name] = cb

            row.add_widget(cb)
            row.add_widget(label)
            items_list.add_widget(row)

        scroll.add_widget(items_list)
        content.add_widget(scroll)

        def on_select_all_toggle(checkbox, value):
            for cb in checkbox_dict.values():
                cb.active = value

        select_all_cb.bind(active=on_select_all_toggle)

        return content

    def _apply_checkbox_filter(self, checkbox_dict, excluded_attr, dialog):
        excluded = set()
        for name, cb in checkbox_dict.items():
            if not cb.active:
                excluded.add(name)

        setattr(self, excluded_attr, excluded)

        if dialog:
            dialog.dismiss()

        self._update_filter_badge()
        self._reload_current_view()

    # ── Date Filter (MDModalDatePicker) ─────────────────────────

    def _show_date_from_picker(self):
        from kivymd.uix.pickers import MDModalDatePicker, MDModalInputDatePicker

        self._date_picker_from = MDModalDatePicker(
            supporting_text=self._("Start Date"),
            text_button_ok=self._("Ok"),
            text_button_cancel=self._("Cancel"),
        )

        self._date_from_clock = Clock.schedule_interval(
            lambda dt: self.translate_date_picker(
                self._date_picker_from, self._date_from_clock), 0)

        self._date_picker_from.bind(
            on_dismiss=lambda x: Clock.unschedule(self._date_from_clock))

        self._date_picker_from.bind(
            on_ok=self._on_date_from_ok,
            on_cancel=self._on_date_from_cancel,
            on_edit=self._on_date_from_switch_to_input,
        )
        self._date_picker_from.open()

    def _on_date_from_ok(self, instance):
        selected = instance.get_date()[0]
        self._filter_date_from = selected.strftime("%Y-%m-%d")
        instance.dismiss()
        Clock.schedule_once(lambda dt: self._show_date_to_picker(), 0.2)

    def _on_date_from_cancel(self, instance):
        instance.dismiss()

    def _on_date_from_switch_to_input(self, instance):
        from kivymd.uix.pickers import MDModalInputDatePicker

        instance.dismiss()
        self._date_input_from = MDModalInputDatePicker(
            supporting_input_text=self._("Start Date"),
            text_button_ok=self._("Ok"),
            text_button_cancel=self._("Cancel"),
            error_text=self._("Invalid date format!"),
        )
        self._date_input_from.bind(
            on_ok=self._on_date_from_ok,
            on_cancel=self._on_date_from_cancel,
            on_edit=lambda x: (x.dismiss(), self._show_date_from_picker()),
        )
        self._date_input_from.open()

    def _show_date_to_picker(self):
        from kivymd.uix.pickers import MDModalDatePicker, MDModalInputDatePicker

        self._date_picker_to = MDModalDatePicker(
            supporting_text=self._("End Date"),
            text_button_ok=self._("Ok"),
            text_button_cancel=self._("Cancel"),
        )

        self._date_to_clock = Clock.schedule_interval(
            lambda dt: self.translate_date_picker(
                self._date_picker_to, self._date_to_clock), 0)

        self._date_picker_to.bind(
            on_dismiss=lambda x: Clock.unschedule(self._date_to_clock))

        self._date_picker_to.bind(
            on_ok=self._on_date_to_ok,
            on_cancel=self._on_date_to_cancel,
            on_edit=self._on_date_to_switch_to_input,
        )
        self._date_picker_to.open()

    def _on_date_to_ok(self, instance):
        selected = instance.get_date()[0]
        self._filter_date_to = selected.strftime("%Y-%m-%d")
        instance.dismiss()
        self._update_filter_badge()
        self._reload_current_view()

    def _on_date_to_cancel(self, instance):
        instance.dismiss()
        self._update_filter_badge()
        self._reload_current_view()

    def _on_date_to_switch_to_input(self, instance):
        from kivymd.uix.pickers import MDModalInputDatePicker

        instance.dismiss()
        self._date_input_to = MDModalInputDatePicker(
            supporting_input_text=self._("End Date"),
            text_button_ok=self._("Ok"),
            text_button_cancel=self._("Cancel"),
            error_text=self._("Invalid date format!"),
        )
        self._date_input_to.bind(
            on_ok=self._on_date_to_ok,
            on_cancel=self._on_date_to_cancel,
            on_edit=lambda x: (x.dismiss(), self._show_date_to_picker()),
        )
        self._date_input_to.open()

    # ── Clear All ───────────────────────────────────────────────

    def clear_all_filters(self):
        self._reset_all_filter_state()
        self._update_filter_badge()
        self._reload_current_view()
        self.show_snackbar(self._("Filters cleared."))

    # ── Badge & Filter Count ────────────────────────────────────

    def _get_active_filter_count(self):
        count = 0
        if self._filter_excluded_courses:
            count += 1
        if self._filter_excluded_schedules:
            count += 1
        if self._filter_date_from or self._filter_date_to:
            count += 1
        if self._group_by_mode:
            count += 1
        return count

    def _update_filter_badge(self):
        try:
            history_screen = self.root.ids.screen_manager.get_screen("HistoryScreen")
            badge = history_screen.ids.filter_badge

            count = self._get_active_filter_count()
            if count > 0:
                badge.text = str(count)
                badge.opacity = 1
            else:
                badge.text = ""
                badge.opacity = 0
        except Exception:
            pass

    # ── Data Loading ────────────────────────────────────────────

    def _reload_current_view(self):
        history_screen = self.root.ids.screen_manager.get_screen("HistoryScreen")
        current_text = history_screen.ids.search_field.text
        self.load_history_to_ui(search_query=current_text)

    def _fetch_history_data(self, search_query=""):
        excluded_courses = (
            list(self._filter_excluded_courses)
            if self._filter_excluded_courses else None
        )
        excluded_schedules = (
            list(self._filter_excluded_schedules)
            if self._filter_excluded_schedules else None
        )
        date_from = self._filter_date_from
        date_to = self._filter_date_to

        has_filters = (
            excluded_courses or excluded_schedules or date_from or date_to
        )

        if search_query.strip() and has_filters:
            return self.db.search_filtered_history(
                search_query, excluded_courses, date_from, date_to,
                excluded_schedules)
        elif search_query.strip():
            return self.db.search_history(search_query)
        elif has_filters:
            return self.db.get_filtered_history(
                excluded_courses, date_from, date_to, excluded_schedules)
        else:
            return self.db.get_history()

    def load_history_to_ui(self, search_query=""):
        self._init_filter_state()

        history_data = self._fetch_history_data(search_query)
        screen = self.root.ids.screen_manager.get_screen("HistoryScreen")

        if self._group_by_mode and self._active_folder_name is None:
            rv_data = self._build_folder_data(history_data)
            screen.ids.rv.viewclass = "FolderCard"
        else:
            if self._active_folder_name is not None:
                history_data = self._filter_by_active_folder(history_data)

            rv_data = self._build_pdf_card_data(history_data)
            screen.ids.rv.viewclass = "PDFHistoryCard"

        screen.ids.rv.data = rv_data

    def _build_folder_data(self, history_data):
        if self._group_by_mode == "course":
            key_index = 5
            folder_type = "course"
        else:
            key_index = 3
            folder_type = "program"

        counts = Counter(record[key_index] for record in history_data)

        rv_data = []
        for name in sorted(counts.keys()):
            rv_data.append({
                "folder_name": name,
                "item_count": str(counts[name]),
                "folder_type": folder_type,
            })
        return rv_data

    def _filter_by_active_folder(self, history_data):
        if self._group_by_mode == "course":
            key_index = 5
        else:
            key_index = 3

        return [r for r in history_data if r[key_index] == self._active_folder_name]

    def _build_pdf_card_data(self, history_data):
        rv_data = []

        months = ["", "Jan", "Feb", "Mar", "Apr", "May",
                  "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        for record in history_data:
            filename, creation_date, filepath, schedule, week, course = record

            file_exists = os.path.exists(filepath)

            try:
                dt_obj = datetime.strptime(creation_date, "%Y-%m-%d %H:%M:%S")
                en_month = months[dt_obj.month]
                translated_month = self._(en_month)
                formatted_date = (
                    f"{dt_obj.day:02d} {translated_month} {dt_obj.year}, "
                    f"{dt_obj.strftime('%H:%M')}"
                )
            except Exception:
                formatted_date = creation_date

            rv_data.append({
                "filename": filename,
                "filepath": filepath,
                "thumbnail": self.get_pdf_thumbnail(filepath) if file_exists else None,
                "course": f"{self._('Course')}: {course}",
                "schedule": f"{self._('Schedule')}: {schedule}",
                "week": f"{self._('Week')}: {week}",
                "date": formatted_date,
                "is_missing": not file_exists,
            })

        return rv_data

    # ── Search ──────────────────────────────────────────────────

    def on_search_text(self, text):
        Clock.unschedule(self._perform_search)
        Clock.schedule_once(lambda dt: self._perform_search(text), 0.3)

    def _perform_search(self, text):
        self.load_history_to_ui(search_query=text)

    # ── File Actions ────────────────────────────────────────────

    def open_file_location(self, filepath):
        open_file_location(filepath)

    def on_card_right_click(self, instance_card, touch, filepath):
        if instance_card.collide_point(*touch.pos):
            if "button" in touch.profile and touch.button == "right":
                self.open_file_location(filepath)
                return True
