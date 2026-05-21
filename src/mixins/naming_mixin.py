from kivy.clock import Clock
from kivy.uix.widget import Widget

from kivymd.uix.dialog import (
    MDDialog, MDDialogHeadlineText,
    MDDialogContentContainer, MDDialogButtonContainer
)
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText
from kivymd.uix.label import MDLabel


DEFAULT_NAMING_FORMATS = [
    {
        "name": "Week First",
        "format_string": "week{week:02d}_{course}",
        "is_preset": True,
        "is_active": True
    },
    {
        "name": "Course First",
        "format_string": "{course}_week{week:02d}",
        "is_preset": True,
        "is_active": False
    },
    {
        "name": "Simple",
        "format_string": "{course}_{week}",
        "is_preset": True,
        "is_active": False
    },
]

DEFAULT_FORMAT_STRING = "week{week:02d}_{course}"


class NamingMixin:
    def _get_naming_formats(self):
        saved = self.get_setting("naming_formats")
        if saved:
            return saved
        return [dict(f) for f in DEFAULT_NAMING_FORMATS]

    def _save_naming_formats(self, formats):
        self.save_setting("naming_formats", formats)

    def get_active_naming_format(self):
        formats = self._get_naming_formats()
        for f in formats:
            if f.get("is_active"):
                return f["format_string"]
        return DEFAULT_FORMAT_STRING

    def _refresh_naming_format_name(self):
        formats = self._get_naming_formats()
        for f in formats:
            if f.get("is_active"):
                name = f["name"]
                if f.get("is_preset"):
                    name = self._(name)
                self.current_naming_format_name = name
                return
        self.current_naming_format_name = self._("Week First")

    def open_naming_format_screen(self):
        screen = self.root.ids.screen_manager.get_screen("NamingFormatScreen")
        screen.load_formats()

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

        sm = self.root.ids.screen_manager
        Clock.schedule_once(lambda dt: setattr(sm, "current", "NamingFormatScreen"), 0)

    def set_active_naming_format(self, index):
        formats = self._get_naming_formats()
        for i, f in enumerate(formats):
            f["is_active"] = (i == index)
        self._save_naming_formats(formats)
        self._refresh_naming_format_name()
        screen = self.root.ids.screen_manager.get_screen("NamingFormatScreen")
        screen.load_formats()

    def show_add_naming_format_dialog(self):
        self._show_naming_format_dialog(edit_index=None)

    def show_edit_naming_format_dialog(self, index):
        self._show_naming_format_dialog(edit_index=index)

    def _show_naming_format_dialog(self, edit_index=None):
        formats = self._get_naming_formats()

        is_edit = edit_index is not None
        initial_name = ""
        initial_format = ""
        if is_edit:
            initial_name = formats[edit_index]["name"]
            initial_format = formats[edit_index]["format_string"]

        content_box = MDBoxLayout(
            orientation="vertical",
            spacing="15dp",
            size_hint_y=None,
            adaptive_height=True,
            padding=(0, "10dp", 0, 0)
        )

        self._naming_name_input = MDTextField(
            mode="outlined",
            text=initial_name,
            multiline=False,
        )
        self._naming_name_input.add_widget(
            MDTextFieldHintText(text=self._("Format Name"))
        )

        self._naming_format_input = MDTextField(
            mode="outlined",
            text=initial_format,
            multiline=False,
        )
        self._naming_format_input.add_widget(
            MDTextFieldHintText(text=self._("Format String"))
        )

        helper_label = MDLabel(
            text=self._("Available variables: {course}, {week}, {schedule}, {num_photos}") + "\n"
                 + self._("Example: {course}_lecture_{week:02d}"),
            theme_text_color="Secondary",
            font_style="Body",
            role="small",
            adaptive_height=True,
        )

        content_box.add_widget(self._naming_name_input)
        content_box.add_widget(self._naming_format_input)
        content_box.add_widget(helper_label)

        cancel_btn = MDButton(style="text")
        cancel_btn.add_widget(MDButtonText(text=self._("Cancel")))
        cancel_btn.bind(on_release=lambda x: self._naming_dialog.dismiss())

        save_text = self._("Update") if is_edit else self._("Save")
        save_btn = MDButton(style="filled")
        save_btn.add_widget(MDButtonText(text=save_text))
        save_btn.bind(
            on_release=lambda x: self._save_naming_format(edit_index)
        )

        title = self._("Edit Format") if is_edit else self._("Add Format")

        self._naming_dialog = MDDialog(
            MDDialogHeadlineText(text=title),
            MDDialogContentContainer(content_box, orientation="vertical"),
            MDDialogButtonContainer(
                Widget(), cancel_btn, save_btn, spacing="8dp"
            ),
        )
        self._naming_dialog.open()

    def _save_naming_format(self, edit_index=None):
        name = self._naming_name_input.text.strip()
        format_string = self._naming_format_input.text.strip()

        if not name:
            self._naming_name_input.error = True
            return

        if not format_string:
            self._naming_format_input.error = True
            return

        try:
            format_string.format(week=1, course="test", schedule="test", num_photos=5)
        except (KeyError, ValueError, IndexError):
            self.show_snackbar(self._("Invalid format string!"))
            return

        formats = self._get_naming_formats()

        if edit_index is not None:
            formats[edit_index]["name"] = name
            formats[edit_index]["format_string"] = format_string
        else:
            new_format = {
                "name": name,
                "format_string": format_string,
                "is_preset": False,
                "is_active": False
            }
            formats.append(new_format)

        self._save_naming_formats(formats)
        self._refresh_naming_format_name()
        self._naming_dialog.dismiss()

        screen = self.root.ids.screen_manager.get_screen("NamingFormatScreen")
        screen.load_formats()

    def confirm_delete_naming_format(self, index):
        formats = self._get_naming_formats()
        format_name = formats[index]["name"]

        cancel_btn = MDButton(style="text")
        cancel_btn.add_widget(MDButtonText(text=self._("Cancel")))
        cancel_btn.bind(
            on_release=lambda x: self._delete_naming_dialog.dismiss()
        )

        delete_btn = MDButton(style="text")
        delete_btn.add_widget(MDButtonText(
            text=self._("Delete"),
            theme_text_color="Custom",
            text_color=[1, 0, 0, 1]
        ))
        delete_btn.bind(
            on_release=lambda x: self._do_delete_naming_format(index)
        )

        msg = f"{self._('Are you sure you want to delete')} '{format_name}'?"

        self._delete_naming_dialog = MDDialog(
            MDDialogHeadlineText(text=self._("Delete Format?")),
            MDDialogContentContainer(
                MDLabel(text=msg),
                orientation="vertical"
            ),
            MDDialogButtonContainer(
                Widget(), cancel_btn, delete_btn, spacing="8dp"
            ),
        )
        self._delete_naming_dialog.open()

    def _do_delete_naming_format(self, index):
        self._delete_naming_dialog.dismiss()
        self._delete_naming_format(index)

    def _delete_naming_format(self, index):
        formats = self._get_naming_formats()
        if index < 0 or index >= len(formats):
            return
        if formats[index].get("is_preset"):
            return

        was_active = formats[index].get("is_active", False)
        formats.pop(index)

        if was_active and formats:
            formats[0]["is_active"] = True

        self._save_naming_formats(formats)
        self._refresh_naming_format_name()

        screen = self.root.ids.screen_manager.get_screen("NamingFormatScreen")
        screen.load_formats()
