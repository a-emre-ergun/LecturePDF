import os
from datetime import datetime

from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.metrics import dp

from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogContentContainer, MDDialogButtonContainer
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel

from src.services.os_utils import open_pdf_file, open_file_location, get_pdf_thumbnail


class HistoryMixin:
    def open_history_screen(self):
        sm = self.root.ids.screen_manager

        history_screen = sm.get_screen("HistoryScreen")
        btn = history_screen.ids.view_toggle_btn
        btn.icon = "view-list" if self.history_view_mode == "grid" else "view-grid"
        history_screen.ids.search_field.text = ""

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

    def load_history_to_ui(self, search_query=""):
        if search_query.strip():
            history_data = self.db.search_history(search_query)
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
