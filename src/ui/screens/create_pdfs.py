import os

from kivy.clock import Clock
from kivy.properties import StringProperty, ListProperty

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.pickers import MDModalDatePicker, MDModalInputDatePicker

from src.services.file_picker import pick_folder, pick_images


class CreatePDFsScreen(MDScreen):
    date_dialog = None
    selected_folder_path = StringProperty(None, allownone=True)
    selected_images_list = ListProperty([])

    def show_date_picker(self):
        app = MDApp.get_running_app()

        self.date_dialog = MDModalDatePicker(
            supporting_text=app.tr._("Select date"),
            text_button_ok=app.tr._("Ok"),
            text_button_cancel=app.tr._("Cancel"))

        self._date_clock = Clock.schedule_interval(
            lambda dt: app.translate_date_picker(self.date_dialog, self._date_clock), 0)

        self.date_dialog.bind(
            on_dismiss=lambda x: Clock.unschedule(self._date_clock))

        self.date_dialog.bind(
            on_ok=self.on_date_save, on_cancel=self.on_date_cancel, on_edit=self.on_switch_to_input_mode)
        self.date_dialog.open()

    def on_date_save(self, instance):
        selected_date = instance.get_date()[0]
        formatted_date = selected_date.strftime("%d.%m.%Y")

        app = MDApp.get_running_app()

        lbl = app.tr._("Start Date")

        self.ids.btn_date_text.text = f"{lbl}: {formatted_date}"
        app.save_setting("semester_start", formatted_date)
        self.date_dialog.dismiss()

    def on_date_cancel(self, instance):
        self.date_dialog.dismiss()

    def on_switch_to_input_mode(self, instance):
        instance.dismiss()

        app = MDApp.get_running_app()

        self.date_dialog = MDModalInputDatePicker(
            supporting_input_text=app.tr._("Enter date"),
            text_button_ok=app.tr._("Ok"),
            text_button_cancel=app.tr._("Cancel"),
            error_text=app.tr._("Invalid date format")
        )
        self.date_dialog.bind(
            on_ok=self.on_date_save,
            on_cancel=self.on_date_cancel,
            on_edit=self.on_switch_to_calendar_mode
        )
        self.date_dialog.open()

    def on_switch_to_calendar_mode(self, instance):
        instance.dismiss()
        self.show_date_picker()

    def open_file_manager(self, mode):
        app = MDApp.get_running_app()

        if mode == "folder":
            if self.selected_images_list:
                msg = app.tr._("Photos already selected! Clear them first.")
                app.show_snackbar(msg)
                return

            path = pick_folder(title=app.tr._("Select Folder"))

            if path:
                self.selected_folder_path = path
                self.ids.btn_folder_text.text = os.path.basename(path)
                self.ids.btn_clear_folder.opacity = 1
                self.ids.btn_clear_folder.disabled = False

        elif mode == "image":
            if self.selected_folder_path:
                msg = app.tr._("Folder already selected! Clear it first.")
                app.show_snackbar(msg)
                return

            files = pick_images(title=app.tr._("Select Photos"))

            if files:
                self.selected_images_list = files
                count = len(files)
                self.ids.btn_photo_text.text = f"{count} {app.tr._('Photos Selected')}"
                self.ids.btn_clear_photos.opacity = 1
                self.ids.btn_clear_photos.disabled = False

    def clear_selection(self, mode):
        app = MDApp.get_running_app()

        if mode == "folder":
            self.selected_folder_path = None
            self.ids.btn_folder_text.text = app.tr._("Select Input Folder")
            self.ids.btn_clear_folder.opacity = 0
            self.ids.btn_clear_folder.disabled = True

        elif mode == "image":
            self.selected_images_list = []
            self.ids.btn_photo_text.text = app.tr._("Select Photos")
            self.ids.btn_clear_photos.opacity = 0
            self.ids.btn_clear_photos.disabled = True
