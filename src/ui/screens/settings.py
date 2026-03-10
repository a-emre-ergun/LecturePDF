from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from src.services.file_picker import pick_folder


class SettingsScreen(MDScreen):
    def select_output_folder(self):
        app = MDApp.get_running_app()

        path = pick_folder(title=app.tr._("Select Output Folder"))

        if path:
            app.custom_output_path = path
            app.save_setting("output_folder", path)


class LanguageScreen(MDScreen):
    pass
