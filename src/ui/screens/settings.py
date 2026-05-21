from kivy.clock import Clock

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from src.services.file_picker import pick_folder


class SettingsScreen(MDScreen):
    def select_output_folder(self):
        app = MDApp.get_running_app()

        pick_folder(
            title=app.tr._("Select Output Folder"),
            on_selection=self._on_output_folder_selected
        )

    def _on_output_folder_selected(self, path):
        if not path:
            return
        Clock.schedule_once(lambda dt: self._apply_output_folder(path))

    def _apply_output_folder(self, path):
        app = MDApp.get_running_app()
        app.custom_output_path = path
        app.save_setting("output_folder", path)

    def reset_output_folder(self):
        app = MDApp.get_running_app()
        app.custom_output_path = ""
        app.save_setting("output_folder", "")


class LanguageScreen(MDScreen):
    def on_pre_enter(self):
        self.opacity = 0

    def on_enter(self):
        Clock.schedule_once(lambda dt: setattr(self, "opacity", 1), 0)
