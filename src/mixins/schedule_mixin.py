import json
import os
import re

from kivy.clock import Clock
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle

from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogContentContainer, MDDialogButtonContainer
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText, MDTextFieldHelperText
from kivymd.uix.label import MDLabel


class ScheduleMixin:
    def show_add_schedule_dialog(self):
        if self.dialog:
            self.dialog = None

        self.sched_name_input = MDTextField()

        hint = MDTextFieldHintText(text=self._("Schedule Name"))

        self.helper_text = MDTextFieldHelperText(
            text=self._("This name already exists!"),
            mode="on_error",
        )
        self.sched_name_input.add_widget(hint)
        self.sched_name_input.add_widget(self.helper_text)

        content = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height="80dp",
            padding="10dp",
        )
        content.add_widget(self.sched_name_input)

        cancel_button = MDButton(style="text")
        cancel_button.add_widget(MDButtonText(text=self._("Cancel")))
        cancel_button.bind(on_release=lambda x: self.dialog.dismiss())

        create_button = MDButton(style="filled")
        create_button.add_widget(MDButtonText(text=self._("Next")))
        create_button.bind(on_release=self.create_schedule_action)

        self.dialog = MDDialog(
            MDDialogHeadlineText(text=self._("Creating a new schedule")),
            MDDialogContentContainer(content, orientation="vertical"),
            MDDialogButtonContainer(
                Widget(),
                cancel_button,
                create_button,
                spacing="8dp",
            ),
            pos_hint={"center_x": 0.5, "top": 0.85},
            size_hint=(0.9, None),
            height="220dp",

        )
        self.dialog.open()

    def create_schedule_action(self, *args):
        name = self.sched_name_input.text.strip()
        if not name:
            return

        for s in self.schedules:
            if s["name"].lower() == name.lower():
                self.sched_name_input.error = True
                return

        clean_name = re.sub(
            r"[^\w\s-]", "", name).strip().replace(" ", "_").lower()
        filename = f"{clean_name}.json"
        full_path = os.path.join(self.project_root, filename)

        new_schedule = {
            "name": name,
            "filename": filename,
            "active": True
        }

        for s in self.schedules:
            s["active"] = False

        self.schedules.append(new_schedule)

        with open(full_path, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)

        self.save_schedule_index()
        self.refresh_schedule_list_ui()
        self.sched_name_input.text = ""
        self.dialog.dismiss()
        self.open_schedule_detail(filename, name)

    def refresh_schedule_list_ui(self):
        try:
            screen = self.root.ids.screen_manager.get_screen("Schedules")
            list_layout = screen.ids.schedule_list
            list_layout.clear_widgets()
            is_dark = self.theme_cls.theme_style == "Dark"

            for s in self.schedules:
                current_fn = s["filename"]
                current_name = s["name"]
                is_active = s["active"]

                if is_active:
                    bg_rgba = self.theme_cls.primaryContainerColor
                    text_color = self.theme_cls.onPrimaryContainerColor
                    status_color = self.theme_cls.onPrimaryContainerColor[:3] + [
                        0.7]

                else:
                    bg_rgba = self.theme_cls.surfaceVariantColor
                    text_color = self.theme_cls.onSurfaceColor
                    status_color = self.theme_cls.onSurfaceVariantColor

                class ScheduleItem(ButtonBehavior, MDBoxLayout):
                    def __init__(self, **kwargs):
                        super().__init__(**kwargs)
                        with self.canvas.before:
                            Color(*bg_rgba)
                            self.rect = RoundedRectangle(
                                size=self.size, pos=self.pos, radius=[12,])
                        self.bind(pos=self.update_rect,
                                  size=self.update_rect)

                    def update_rect(self, *args):
                        self.rect.pos = self.pos
                        self.rect.size = self.size
                card = ScheduleItem(
                    orientation="horizontal",
                    size_hint=(1, None),
                    height="72dp",
                    padding="12dp",
                    spacing="8dp",
                )
                card.bind(on_release=lambda x,
                          fn=current_fn: self.set_active_schedule(fn))
                text_box = MDBoxLayout(
                    orientation="vertical",
                    adaptive_height=True,
                    pos_hint={"center_y": .5},
                )
                lbl_name = MDLabel(
                    text=current_name,
                    bold=True,
                    theme_text_color="Custom",
                    text_color=text_color,
                    adaptive_height=True,
                    font_style="Title",
                    role="medium",
                )
                lbl_status = MDLabel(
                    text=self._("Active") if is_active else self._(
                        "Click to activate"),
                    theme_text_color="Custom",
                    text_color=status_color,
                    adaptive_height=True,
                    font_style="Label",
                    role="large",
                )
                text_box.add_widget(lbl_name)
                text_box.add_widget(lbl_status)

                buttons_box = MDBoxLayout(
                    orientation="horizontal",
                    adaptive_width=True,
                    spacing="4dp",
                    pos_hint={"center_y": .5},
                )
                delete_btn = MDIconButton(
                    icon="trash-can-outline",
                    theme_icon_color="Custom",
                    icon_color="red",
                    pos_hint={"center_y": .5},
                )
                delete_btn.bind(on_release=lambda x, fn=current_fn,
                                nm=current_name: self.confirm_delete_schedule(fn, nm))

                edit_btn = MDIconButton(
                    icon="pencil",
                    theme_icon_color="Custom",
                    icon_color=text_color,
                    pos_hint={"center_y": .5},
                )
                edit_btn.bind(on_release=lambda x, fn=current_fn,
                              nm=current_name: self.open_schedule_detail(fn, nm))

                buttons_box.add_widget(delete_btn)
                buttons_box.add_widget(edit_btn)

                card.add_widget(text_box)
                card.add_widget(buttons_box)

                list_layout.add_widget(card)

            spacer = Widget(size_hint_y=None, height="50dp")
            list_layout.add_widget(spacer)

        except Exception as e:
            import traceback
            traceback.print_exc()

    def load_schedule_index(self):
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r") as f:
                    self.schedules = json.load(f)
            except:
                self.schedules = []
        else:
            self.schedules = []

    def save_schedule_index(self):
        with open(self.index_file, "w") as f:
            json.dump(self.schedules, f, indent=2)

    def set_active_schedule(self, filename):
        for s in self.schedules:
            s["active"] = (s["filename"] == filename)
        self.save_schedule_index()
        self.refresh_schedule_list_ui()

    def confirm_delete_schedule(self, filename, name):
        self.schedule_to_delete = filename

        cancel_btn = MDButton(style="text")
        cancel_btn.add_widget(MDButtonText(text=self._("Cancel")))
        cancel_btn.bind(on_release=lambda x: self.delete_dialog.dismiss())

        delete_btn = MDButton(style="text")
        delete_btn.add_widget(MDButtonText(
            text=self._("Delete"), theme_text_color="Custom", text_color=[1, 0, 0, 1]))
        delete_btn.bind(on_release=self.delete_schedule_action)

        msg_part = self._("Are you sure you want to delete")
        full_msg = f"{msg_part} '{name}'?"

        self.delete_dialog = MDDialog(
            MDDialogHeadlineText(text=self._("Delete Schedule?")),
            MDDialogContentContainer(
                MDLabel(
                    text=full_msg,
                ),
                orientation="vertical"
            ),
            MDDialogButtonContainer(
                Widget(),
                cancel_btn,
                delete_btn,
                spacing="8dp",
            ),
        )
        self.delete_dialog.open()

    def delete_schedule_action(self, *args):
        if not hasattr(self, "schedule_to_delete"):
            return

        filename = self.schedule_to_delete
        full_path = os.path.join(self.project_root, filename)

        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except Exception as e:
                print(f"Error deleting file: {e}")

        self.schedules = [
            s for s in self.schedules if s["filename"] != filename]

        self.save_schedule_index()
        self.refresh_schedule_list_ui()

        self.delete_dialog.dismiss()

    def open_schedule_detail(self, filename, name):
        sm = self.root.ids.screen_manager
        detail_screen = sm.get_screen("ScheduleDetail")

        detail_screen.schedule_name = name
        detail_screen.schedule_filename = filename

        self.load_courses_to_ui(filename)

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

        Clock.schedule_once(lambda dt: setattr(sm, "current", "ScheduleDetail"), 0)

    def go_back_to_schedules(self):
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

        self.toggle_fab(True)

        Clock.schedule_once(lambda dt: setattr(sm, "current", "Schedules"), 0)
