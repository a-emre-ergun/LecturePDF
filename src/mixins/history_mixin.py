import os
from datetime import datetime

from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.metrics import dp

from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogContentContainer, MDDialogButtonContainer
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDListItem, MDListItemLeadingIcon, MDListItemSupportingText
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu

from src.services.os_utils import open_pdf_file, open_file_location, get_pdf_thumbnail


class HistoryMixin:
    def _init_filter_state(self):
        if not hasattr(self, '_filter_excluded_courses'):
            self._filter_excluded_courses = set()
        if not hasattr(self, '_filter_date_from'):
            self._filter_date_from = None
        if not hasattr(self, '_filter_date_to'):
            self._filter_date_to = None
        if not hasattr(self, '_filter_menu'):
            self._filter_menu = None
        if not hasattr(self, '_course_filter_dialog'):
            self._course_filter_dialog = None
        if not hasattr(self, '_date_filter_dialog'):
            self._date_filter_dialog = None
        if not hasattr(self, '_course_checkboxes'):
            self._course_checkboxes = {}

    def open_history_screen(self):
        self._init_filter_state()

        sm = self.root.ids.screen_manager

        history_screen = sm.get_screen("HistoryScreen")
        btn = history_screen.ids.view_toggle_btn
        btn.icon = "view-list" if self.history_view_mode == "grid" else "view-grid"
        history_screen.ids.search_field.text = ""

        self._filter_excluded_courses = set()
        self._filter_date_from = None
        self._filter_date_to = None
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

            history_screen = self.root.ids.screen_manager.get_screen(
                "HistoryScreen")
            current_text = history_screen.ids.search_field.text
            self.load_history_to_ui(search_query=current_text)

            self.show_snackbar(self._("Record removed successfully!"))

        if hasattr(self, "missing_dialog"):
            self.missing_dialog.dismiss()

    # ── Filter Methods ──────────────────────────────────────────

    def show_filter_menu(self, caller):
        self._init_filter_state()

        if self._filter_menu:
            self._filter_menu.dismiss()
            self._filter_menu = None

        active_count = self._get_active_filter_count()
        clear_text = self._("Clear Filters")

        menu_items = [
            {
                "text": self._("Filter by Course"),
                "leading_icon": "book-outline",
                "on_release": lambda: self._on_filter_menu_select("course"),
            },
            {
                "text": self._("Filter by Date"),
                "leading_icon": "calendar-range",
                "on_release": lambda: self._on_filter_menu_select("date"),
            },
        ]

        if active_count > 0:
            menu_items.append({
                "text": clear_text,
                "leading_icon": "filter-remove-outline",
                "on_release": lambda: self._on_filter_menu_select("clear"),
            })

        self._filter_menu = MDDropdownMenu(
            caller=caller,
            items=menu_items,
        )
        self._filter_menu.open()

    def _on_filter_menu_select(self, filter_type):
        if self._filter_menu:
            self._filter_menu.dismiss()
            self._filter_menu = None

        if filter_type == "course":
            Clock.schedule_once(lambda dt: self.show_course_filter_dialog(), 0.1)
        elif filter_type == "date":
            Clock.schedule_once(lambda dt: self.show_date_filter_dialog(), 0.1)
        elif filter_type == "clear":
            self.clear_all_filters()

    def show_course_filter_dialog(self):
        all_courses = self.db.get_distinct_courses()

        if not all_courses:
            self.show_snackbar(self._("No courses found in history."))
            return

        self._course_checkboxes = {}

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

        all_active = len(self._filter_excluded_courses) == 0

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

        from kivy.uix.scrollview import ScrollView

        scroll = ScrollView(
            size_hint_y=None,
            height=min(len(all_courses) * dp(48), dp(300)),
        )
        course_list = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            spacing=dp(2),
        )

        for course_name in all_courses:
            row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(48),
                padding=[dp(16), 0, dp(16), 0],
                spacing=dp(12),
            )

            is_active = course_name not in self._filter_excluded_courses

            cb = MDCheckbox(
                size_hint=(None, None),
                size=(dp(24), dp(24)),
                pos_hint={"center_y": 0.5},
                active=is_active,
            )
            label = MDLabel(
                text=course_name,
                theme_font_size="Custom",
                font_size="15sp",
                pos_hint={"center_y": 0.5},
                adaptive_height=True,
            )

            self._course_checkboxes[course_name] = cb

            row.add_widget(cb)
            row.add_widget(label)
            course_list.add_widget(row)

        scroll.add_widget(course_list)
        content.add_widget(scroll)

        def on_select_all_toggle(checkbox, value):
            for cb in self._course_checkboxes.values():
                cb.active = value

        select_all_cb.bind(active=on_select_all_toggle)

        cancel_btn = MDButton(style="text")
        cancel_btn.add_widget(MDButtonText(text=self._("Cancel")))
        cancel_btn.bind(on_release=lambda x: self._course_filter_dialog.dismiss())

        apply_btn = MDButton(style="text")
        apply_btn.add_widget(MDButtonText(text=self._("Apply")))
        apply_btn.bind(on_release=lambda x: self.apply_course_filter())

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

    def apply_course_filter(self):
        self._filter_excluded_courses = set()

        for course_name, cb in self._course_checkboxes.items():
            if not cb.active:
                self._filter_excluded_courses.add(course_name)

        if self._course_filter_dialog:
            self._course_filter_dialog.dismiss()
            self._course_filter_dialog = None

        self._update_filter_badge()

        history_screen = self.root.ids.screen_manager.get_screen("HistoryScreen")
        current_text = history_screen.ids.search_field.text
        self.load_history_to_ui(search_query=current_text)

    def show_date_filter_dialog(self):
        from kivymd.uix.textfield import MDTextField

        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(16),
            adaptive_height=True,
            padding=[dp(8), dp(16), dp(8), dp(8)],
        )

        info_label = MDLabel(
            text=self._("Enter dates in YYYY-MM-DD format:"),
            theme_font_size="Custom",
            font_size="14sp",
            adaptive_height=True,
            theme_text_color="Secondary",
        )
        content.add_widget(info_label)

        self._date_from_field = MDTextField(
            mode="outlined",
            size_hint_x=1,
        )
        self._date_from_field.hint_text = self._("Start Date") + " (YYYY-MM-DD)"
        if self._filter_date_from:
            self._date_from_field.text = self._filter_date_from
        content.add_widget(self._date_from_field)

        self._date_to_field = MDTextField(
            mode="outlined",
            size_hint_x=1,
        )
        self._date_to_field.hint_text = self._("End Date") + " (YYYY-MM-DD)"
        if self._filter_date_to:
            self._date_to_field.text = self._filter_date_to
        content.add_widget(self._date_to_field)

        cancel_btn = MDButton(style="text")
        cancel_btn.add_widget(MDButtonText(text=self._("Cancel")))
        cancel_btn.bind(on_release=lambda x: self._date_filter_dialog.dismiss())

        apply_btn = MDButton(style="text")
        apply_btn.add_widget(MDButtonText(text=self._("Apply")))
        apply_btn.bind(on_release=lambda x: self.apply_date_filter())

        self._date_filter_dialog = MDDialog(
            MDDialogHeadlineText(text=self._("Filter by Date")),
            MDDialogContentContainer(
                content,
                orientation="vertical",
            ),
            MDDialogButtonContainer(
                Widget(), cancel_btn, apply_btn, spacing="8dp"),
        )
        self._date_filter_dialog.open()

    def apply_date_filter(self):
        date_from = self._date_from_field.text.strip()
        date_to = self._date_to_field.text.strip()

        if date_from:
            try:
                datetime.strptime(date_from, "%Y-%m-%d")
                self._filter_date_from = date_from
            except ValueError:
                self.show_snackbar(self._("Invalid date format! Use YYYY-MM-DD."))
                return
        else:
            self._filter_date_from = None

        if date_to:
            try:
                datetime.strptime(date_to, "%Y-%m-%d")
                self._filter_date_to = date_to
            except ValueError:
                self.show_snackbar(self._("Invalid date format! Use YYYY-MM-DD."))
                return
        else:
            self._filter_date_to = None

        if self._date_filter_dialog:
            self._date_filter_dialog.dismiss()
            self._date_filter_dialog = None

        self._update_filter_badge()

        history_screen = self.root.ids.screen_manager.get_screen("HistoryScreen")
        current_text = history_screen.ids.search_field.text
        self.load_history_to_ui(search_query=current_text)

    def clear_all_filters(self):
        self._filter_excluded_courses = set()
        self._filter_date_from = None
        self._filter_date_to = None
        self._update_filter_badge()

        history_screen = self.root.ids.screen_manager.get_screen("HistoryScreen")
        current_text = history_screen.ids.search_field.text
        self.load_history_to_ui(search_query=current_text)

        self.show_snackbar(self._("Filters cleared."))

    def _get_active_filter_count(self):
        count = 0
        if self._filter_excluded_courses:
            count += 1
        if self._filter_date_from or self._filter_date_to:
            count += 1
        return count

    def _update_filter_badge(self):
        try:
            history_screen = self.root.ids.screen_manager.get_screen("HistoryScreen")
            filter_btn = history_screen.ids.filter_btn
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

    def load_history_to_ui(self, search_query=""):
        self._init_filter_state()

        excluded = list(self._filter_excluded_courses) if self._filter_excluded_courses else None
        date_from = self._filter_date_from
        date_to = self._filter_date_to

        has_filters = excluded or date_from or date_to

        if search_query.strip() and has_filters:
            history_data = self.db.search_filtered_history(
                search_query, excluded, date_from, date_to)
        elif search_query.strip():
            history_data = self.db.search_history(search_query)
        elif has_filters:
            history_data = self.db.get_filtered_history(
                excluded, date_from, date_to)
        else:
            history_data = self.db.get_history()

        screen = self.root.ids.screen_manager.get_screen("HistoryScreen")

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
                formatted_date = f"{dt_obj.day:02d} {translated_month} {dt_obj.year}, {dt_obj.strftime('%H:%M')}"
            except:
                formatted_date = creation_date

            rv_data.append({
                "filename": filename,
                "filepath": filepath,
                "thumbnail": self.get_pdf_thumbnail(filepath) if file_exists else None,
                "course": f"{self._('Course')}: {course}",
                "schedule": f"{self._('Schedule')}: {schedule}",
                "week": f"{self._('Week')}: {week}",
                "date": formatted_date,
                "is_missing": not file_exists
            })

        screen.ids.rv.data = rv_data

    def on_search_text(self, text):
        Clock.unschedule(self._perform_search)
        Clock.schedule_once(lambda dt: self._perform_search(text), 0.3)

    def _perform_search(self, text):
        self.load_history_to_ui(search_query=text)

    def open_file_location(self, filepath):
        open_file_location(filepath)

    def on_card_right_click(self, instance_card, touch, filepath):
        if instance_card.collide_point(*touch.pos):
            if "button" in touch.profile and touch.button == "right":
                self.open_file_location(filepath)
                return True
