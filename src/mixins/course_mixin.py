import json
import os

from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle

from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogContentContainer, MDDialogButtonContainer
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton, MDButtonIcon
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.anchorlayout import MDAnchorLayout
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.pickers import MDTimePickerDialVertical, MDTimePickerInput


class CourseMixin:
    def load_courses_to_ui(self, filename):
        detail_screen = self.root.ids.screen_manager.get_screen(
            "ScheduleDetail")
        content_layout = detail_screen.ids.detail_content
        content_layout.clear_widgets()

        full_path = os.path.join(self.project_root, filename)
        temp_course_names = []

        if not os.path.exists(full_path):
            return

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                courses_by_day = {i: [] for i in range(7)}

                for course_name, sessions in data.items():
                    if course_name == "schedule_name":
                        continue

                    temp_course_names.append(course_name)

                    if not isinstance(sessions, list):
                        continue

                    for session in sessions:
                        day_idx = session.get("day")
                        session_data = session.copy()
                        session_data["course_name"] = course_name

                        if "color" not in session_data:
                            session_data["color"] = "039BE5"

                        if day_idx is not None and 0 <= day_idx <= 6:
                            courses_by_day[day_idx].append(session_data)

                self.past_courses_map[filename] = list(set(temp_course_names))
                for day_idx in range(7):
                    day_sessions = courses_by_day[day_idx]

                    if day_sessions:
                        day_name = self.day_int_to_str[day_idx]
                        self.add_day_header(day_name, content_layout)

                        day_sessions.sort(
                            key=lambda x: x.get("start_time", "00:00"))

                        for session in day_sessions:
                            self.add_course_card_widget(
                                session, content_layout)

                        content_layout.add_widget(
                            Widget(size_hint_y=None, height="10dp"))

        except Exception as e:
            print(f"Error loading courses: {e}")
            import traceback
            traceback.print_exc()

    def add_day_header(self, day_name, parent_layout):
        translated_day_name = self._(day_name)

        header_box = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            padding=("4dp", "0dp", "0dp", "8dp")
        )
        lbl = MDLabel(
            text=translated_day_name,
            bold=True,
            font_style="Headline",
            role="small",
            theme_text_color="Primary",
            adaptive_height=True
        )
        header_box.add_widget(lbl)
        parent_layout.add_widget(header_box)

    def add_course_card_widget(self, course_data, parent_layout):
        bg_color = get_color_from_hex(course_data.get("color", "039BE5"))

        card = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="90dp",
            padding=("16dp", "8dp", "8dp", "8dp"),
            spacing="8dp",
            radius=[16, 16, 16, 16],
        )

        with card.canvas.before:
            Color(*bg_color)
            RoundedRectangle(pos=card.pos, size=card.size, radius=[16,])

        def update_card_rect(instance, value):
            instance.canvas.before.clear()
            with instance.canvas.before:
                Color(*bg_color)
                RoundedRectangle(pos=instance.pos,
                                 size=instance.size, radius=[16,])
        card.bind(pos=update_card_rect, size=update_card_rect)

        text_box = MDBoxLayout(
            orientation="vertical",
            spacing="4dp",
            pos_hint={"center_y": .5},
            adaptive_height=True
        )

        lbl_name = MDLabel(
            text=course_data.get("course_name", self._("Unknown")),
            bold=True,
            font_style="Title",
            role="medium",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            shorten=True,
            shorten_from="right",
            adaptive_height=True
        )

        lbl_time = MDLabel(
            text=f"{course_data.get("start_time", "")} - {course_data.get("end_time", "")}",
            font_style="Label",
            role="large",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 0.9),
            adaptive_height=True
        )

        text_box.add_widget(lbl_name)
        text_box.add_widget(lbl_time)

        actions_box = MDBoxLayout(
            orientation="horizontal",
            adaptive_size=True,
            spacing="2dp",
            pos_hint={"center_y": .5}
        )

        btn_edit = MDIconButton(
            icon="pencil-outline",
            theme_icon_color="Custom",
            icon_color=(1, 1, 1, 1),
            style="standard",
        )
        btn_edit.bind(
            on_release=lambda x: self.edit_course_session(course_data))

        btn_delete = MDIconButton(
            icon="trash-can-outline",
            theme_icon_color="Custom",
            icon_color=(1, 1, 1, 1),
            style="standard",
        )
        btn_delete.bind(
            on_release=lambda x: self.confirm_delete_course(course_data))

        actions_box.add_widget(btn_delete)
        actions_box.add_widget(btn_edit)

        card.add_widget(text_box)
        card.add_widget(actions_box)

        parent_layout.add_widget(card)

    def check_conflict(self, day_int, start_min, end_min, data, ignore_session=None):
        for course_name, sessions in data.items():
            if not isinstance(sessions, list):
                continue

            for session in sessions:
                if ignore_session:
                    if (course_name == ignore_session.get("course_name") and
                        session.get("day") == ignore_session.get("day") and
                            session.get("start_time") == ignore_session.get("start_time")):
                        continue

                if session.get("day") != day_int:
                    continue

                exist_s_h, exist_s_m = map(
                    int, session["start_time"].split(":"))
                exist_e_h, exist_e_m = map(int, session["end_time"].split(":"))

                exist_start = exist_s_h * 60 + exist_s_m
                exist_end = exist_e_h * 60 + exist_e_m

                if (start_min < exist_end) and (end_min > exist_start):
                    return True, course_name

        return False, None

    def open_day_picker(self, instance):
        content_box = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            spacing="12dp",
            padding=("0dp", "10dp", "0dp", "10dp")
        )

        row_top = MDBoxLayout(
            orientation="horizontal",
            adaptive_size=True,
            spacing="6dp",
            pos_hint={"center_x": .5}
        )

        row_bottom = MDBoxLayout(
            orientation="horizontal",
            adaptive_size=True,
            spacing="6dp",
            pos_hint={"center_x": .5}
        )

        for index, abbr in enumerate(self.days_abbr_list):
            translated_abbr = self._(abbr)
            full_name = self.day_int_to_str[index]
            is_selected = (self.selected_day == full_name)

            btn_style = "filled" if is_selected else "outlined"

            btn = MDButton(
                style=btn_style,
                size_hint=(None, None),
                size=(dp(56), dp(40))
            )

            btn.add_widget(MDButtonText(
                text=translated_abbr, font_style="Label", role="large"))

            btn.bind(on_release=lambda x, d=full_name: self.select_day(d))

            if index < 4:
                row_top.add_widget(btn)
            else:
                row_bottom.add_widget(btn)

        content_box.add_widget(row_top)
        content_box.add_widget(row_bottom)

        self.day_picker_dialog = MDDialog(
            MDDialogHeadlineText(text=self._("Select Day"),
                                 pos_hint={"center_x": .5}),
            MDDialogContentContainer(content_box, orientation="vertical"),
            size_hint_x=0.9,
        )
        self.day_picker_dialog.open()

    def select_day(self, day_full_name):
        self.selected_day = day_full_name

        if hasattr(self, "btn_day_text"):
            self.btn_day_text.text = self._(day_full_name)

        if self.day_picker_dialog:
            self.day_picker_dialog.dismiss()

    def show_time_picker(self, time_type):
        time_dialog = MDTimePickerDialVertical(headline_text=self._("Select Time"),
                                               text_button_ok=self._("Ok"),
                                               text_button_cancel=self._("Cancel"))

        time_dialog.bind(on_ok=lambda x: self.set_time(x, time_type))
        time_dialog.bind(on_cancel=lambda x: x.dismiss())
        time_dialog.bind(
            on_edit=lambda x: self.switch_to_input_mode(x, time_type))
        time_dialog.open()

    def switch_to_input_mode(self, current_dialog, time_type):
        current_dialog.dismiss()

        input_dialog = MDTimePickerInput(headline_text=self._("Select Time"),
                                         text_button_ok=self._("Ok"),
                                         text_button_cancel=self._("Cancel")
                                         )

        self.translate_time_picker(input_dialog)

        input_dialog.bind(on_ok=lambda x: self.set_time(x, time_type))
        input_dialog.bind(on_cancel=lambda x: x.dismiss())
        input_dialog.bind(
            on_edit=lambda x: self.switch_to_dial_mode(x, time_type))
        input_dialog.open()

    def translate_time_picker(self, widget):
        for child in widget.children:
            if hasattr(child, "text"):
                if child.text == "Hour":
                    child.text = self.tr._("Hour")
                elif child.text == "Minute":
                    child.text = self.tr._("Minute")

            if child.children:
                self.translate_time_picker(child)

    def switch_to_dial_mode(self, current_dialog, time_type):
        current_dialog.dismiss()
        self.show_time_picker(time_type)

    def set_time(self, instance_time_picker, time_type):
        selected_time_str = instance_time_picker.time.strftime("%H:%M")

        if time_type == "start":
            self.start_time = selected_time_str
            self.lbl_start_time.text = selected_time_str
            self.btn_start_time.line_color = self.theme_cls.outlineColor
        elif time_type == "end":
            self.end_time = selected_time_str
            self.lbl_end_time.text = selected_time_str
            self.btn_end_time.line_color = self.theme_cls.outlineColor

        instance_time_picker.dismiss()

    def open_color_picker(self, instance):
        grid = MDGridLayout(cols=4, spacing="12dp", adaptive_height=True,
                            padding="10dp", adaptive_size=True, pos_hint={"center_x": .5})
        for color_hex in self.color_palette:
            icon_name = "check-circle" if color_hex == self.selected_color_hex else "circle"
            btn = MDIconButton(
                icon=icon_name, theme_icon_color="Custom", icon_color=get_color_from_hex(color_hex), font_size="32dp"
            )
            btn.bind(on_release=lambda x, c=color_hex: self.select_color(c))
            grid.add_widget(btn)

        self.color_picker_dialog = MDDialog(
            MDDialogHeadlineText(text=self._("Select Course Color")),
            MDDialogContentContainer(grid, orientation="vertical"),
            size_hint=(0.8, None),
        )
        self.color_picker_dialog.open()

    def select_color(self, color_hex):
        self.selected_color_hex = color_hex
        if hasattr(self, "color_button"):
            self.color_button.icon_color = get_color_from_hex(color_hex)
        if self.color_picker_dialog:
            self.color_picker_dialog.dismiss()

    def edit_course_session(self, session_data):
        self.show_add_course_dialog(edit_data=session_data)

    def show_add_course_dialog(self, edit_data=None):
        if edit_data:
            self.is_editing = True
            self.editing_original_data = edit_data

            self.selected_color_hex = edit_data.get("color", "039BE5")
            day_int = edit_data.get("day", 0)
            self.selected_day = self.day_int_to_str.get(day_int, "Monday")
            self.start_time = edit_data.get("start_time")
            self.end_time = edit_data.get("end_time")
            course_name_text = edit_data.get("course_name", "")
        else:
            self.is_editing = False
            self.editing_original_data = None
            self.selected_color_hex = "039BE5"
            self.selected_day = None
            self.start_time = None
            self.end_time = None
            course_name_text = ""

        current_screen = self.root.ids.screen_manager.get_screen(
            "ScheduleDetail")
        filename = current_screen.schedule_filename
        current_courses = self.past_courses_map.get(filename, [])

        content_box = MDBoxLayout(
            orientation="vertical",
            spacing="15dp",
            size_hint_y=None,
            adaptive_height=True,
            padding=(0, "10dp", 0, 0)
        )

        row_1 = MDBoxLayout(orientation="horizontal",
                            spacing="5dp", size_hint_y=None, height="50dp")

        self.course_name_input = MDTextField(
            mode="outlined", size_hint_x=0.6, pos_hint={"center_y": .5}, multiline=False,
            text=course_name_text)
        self.course_name_input.add_widget(
            MDTextFieldHintText(text=self._("Course Name")))

        self.color_button = MDIconButton(
            icon="circle", theme_icon_color="Custom",
            icon_color=get_color_from_hex(self.selected_color_hex), pos_hint={"center_y": .5}
        )
        self.color_button.bind(on_release=self.open_color_picker)

        arrow_button = MDIconButton(
            icon="chevron-down", pos_hint={"center_y": .5},
            theme_icon_color="Custom", icon_color=self.theme_cls.primaryColor
        )
        menu_items = [{"text": c, "on_release": lambda x=c: self.set_course_from_menu(
            x)} for c in current_courses]

        self.dropdown_menu = MDDropdownMenu(
            caller=arrow_button, items=menu_items, position="bottom", width_mult=4, max_height="240dp")
        arrow_button.bind(on_release=lambda x: self.dropdown_menu.open())

        row_1.add_widget(self.course_name_input)
        row_1.add_widget(self.color_button)
        row_1.add_widget(arrow_button)

        row_2 = MDAnchorLayout(
            size_hint_y=None,
            height="50dp",
            anchor_x="center"
        )

        btn_day = MDButton(
            style="outlined",
            size_hint=(None, None),
            height=dp(48),
            width=dp(200),
        )

        if self.selected_day:
            day_label = self._(self.selected_day)
        else:
            day_label = self._("Select Day")

        self.btn_day_text = MDButtonText(text=day_label)

        btn_day.add_widget(MDButtonIcon(icon="calendar-week"))
        btn_day.add_widget(self.btn_day_text)

        btn_day.bind(on_release=self.open_day_picker)
        row_2.add_widget(btn_day)

        row_3 = MDBoxLayout(
            orientation="horizontal",
            spacing="12dp",
            size_hint_y=None,
            height="50dp",
            adaptive_width=True,
            pos_hint={"center_x": .5}
        )

        self.btn_start_time = MDButton(
            style="outlined",
            size_hint=(None, None),
            size=(dp(100), dp(42)),
            pos_hint={"center_y": .5}
        )
        self.btn_start_time.add_widget(
            MDButtonIcon(icon="clock-time-four-outline"))

        start_label = self.start_time if self.start_time else self._("Start")
        self.lbl_start_time = MDButtonText(text=start_label)

        self.btn_start_time.add_widget(self.lbl_start_time)
        self.btn_start_time.bind(
            on_release=lambda x: self.show_time_picker("start"))

        self.btn_end_time = MDButton(
            style="outlined",
            size_hint=(None, None),
            size=(dp(100), dp(42)),
            pos_hint={"center_y": .5}
        )
        self.btn_end_time.add_widget(
            MDButtonIcon(icon="clock-time-eight-outline"))

        end_label = self.end_time if self.end_time else self._("End")
        self.lbl_end_time = MDButtonText(text=end_label)

        self.btn_end_time.add_widget(self.lbl_end_time)
        self.btn_end_time.bind(
            on_release=lambda x: self.show_time_picker("end"))

        row_3.add_widget(self.btn_start_time)
        row_3.add_widget(self.btn_end_time)

        content_box.add_widget(row_1)
        content_box.add_widget(row_2)
        content_box.add_widget(row_3)

        cancel_btn = MDButton(style="text")
        cancel_btn.add_widget(MDButtonText(text=self._("Cancel")))
        cancel_btn.bind(on_release=lambda x: self.course_dialog.dismiss())

        save_btn_text = self._("Update") if self.is_editing else self._("Save")
        save_btn = MDButton(style="filled")
        save_btn.add_widget(MDButtonText(text=save_btn_text))
        save_btn.bind(on_release=self.save_course_action)

        title_text = self._(
            "Edit Course") if self.is_editing else self._("Add Course")

        self.course_dialog = MDDialog(
            MDDialogHeadlineText(
                text=title_text),
            MDDialogContentContainer(content_box, orientation="vertical"),
            MDDialogButtonContainer(
                Widget(), cancel_btn, save_btn, spacing="8dp"),
        )
        self.course_dialog.open()

    def set_course_from_menu(self, text_item):
        self.course_name_input.text = text_item
        self.dropdown_menu.dismiss()

    def save_course_action(self, *args):
        course_name = self.course_name_input.text.strip()

        if not course_name:
            self.course_name_input.error = True
            return

        if not self.selected_day:
            lbl_select = self._("Select Day")
            lbl_req = self._("Required!")
            self.btn_day_text.text = f"{lbl_select} ({lbl_req})"
            return

        if not self.start_time or not self.end_time:
            req_text = self._("Required!")
            if not self.start_time:
                self.lbl_start_time.text = req_text
            if not self.end_time:
                self.lbl_end_time.text = req_text
            return

        s_h, s_m = map(int, self.start_time.split(":"))
        e_h, e_m = map(int, self.end_time.split(":"))

        start_minutes = s_h * 60 + s_m
        end_minutes = e_h * 60 + e_m

        if end_minutes <= start_minutes:
            self.lbl_end_time.text = self._("Invalid!")
            self.btn_end_time.line_color = "red"
            return

        day_int = self.day_str_to_int.get(self.selected_day, 0)

        current_screen = self.root.ids.screen_manager.get_screen(
            "ScheduleDetail")
        filename = current_screen.schedule_filename
        full_path = os.path.join(self.project_root, filename)

        ignore_data = None
        if hasattr(self, "is_editing") and self.is_editing and self.editing_original_data:
            ignore_data = self.editing_original_data

        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                is_conflict, conflict_course = self.check_conflict(
                    day_int, start_minutes, end_minutes, data, ignore_session=ignore_data)

                if is_conflict:
                    msg = self._("Conflict with")
                    self.show_snackbar(f"{msg} '{conflict_course}'!")
                    return

                if hasattr(self, "is_editing") and self.is_editing and self.editing_original_data:
                    old_name = self.editing_original_data.get("course_name")
                    old_day = self.editing_original_data.get("day")
                    old_start = self.editing_original_data.get("start_time")

                    if old_name in data:
                        sessions = data[old_name]
                        data[old_name] = [
                            s for s in sessions
                            if not (s.get("day") == old_day and s.get("start_time") == old_start)
                        ]
                        if not data[old_name]:
                            del data[old_name]

                new_session = {
                    "day": day_int,
                    "start_time": self.start_time,
                    "end_time": self.end_time,
                    "color": self.selected_color_hex
                }

                if course_name not in data:
                    data[course_name] = []

                data[course_name].append(new_session)

                with open(full_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                    f.truncate()
            except Exception as e:
                print(f"Error saving course: {e}")

        if course_name not in self.past_courses:
            self.past_courses.append(course_name)

        self.course_dialog.dismiss()
        self.load_courses_to_ui(filename)

    def confirm_delete_course(self, session_data):
        self.session_to_delete = session_data

        cancel_btn = MDButton(style="text")
        cancel_btn.add_widget(MDButtonText(text=self._("Cancel")))
        cancel_btn.bind(
            on_release=lambda x: self.delete_course_dialog.dismiss())

        delete_btn = MDButton(style="text")
        delete_btn.add_widget(MDButtonText(
            text=self._("Delete"), theme_text_color="Custom", text_color=[1, 0, 0, 1]))
        delete_btn.bind(on_release=self.delete_course_action)

        course_name = session_data.get("course_name")
        msg_part1 = self._("Are you sure you want to delete")
        msg_full = f"{msg_part1} '{course_name}'?"

        self.delete_course_dialog = MDDialog(
            MDDialogHeadlineText(text=self._("Delete Course?")),
            MDDialogContentContainer(
                MDLabel(
                    text=msg_full,
                ),
                orientation="vertical"
            ),
            MDDialogButtonContainer(
                Widget(), cancel_btn, delete_btn, spacing="8dp"),
        )
        self.delete_course_dialog.open()

    def delete_course_action(self, *args):
        if not hasattr(self, "session_to_delete"):
            return

        target_course = self.session_to_delete.get("course_name")
        target_day = self.session_to_delete.get("day")
        target_start = self.session_to_delete.get("start_time")

        current_screen = self.root.ids.screen_manager.get_screen(
            "ScheduleDetail")
        filename = current_screen.schedule_filename
        full_path = os.path.join(self.project_root, filename)

        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if target_course in data:
                    sessions = data[target_course]
                    new_sessions = [
                        s for s in sessions
                        if not (s.get("day") == target_day and s.get("start_time") == target_start)
                    ]

                    if not new_sessions:
                        del data[target_course]
                    else:
                        data[target_course] = new_sessions

                    with open(full_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4)
                        f.truncate()

                self.load_courses_to_ui(filename)

            except Exception as e:
                print(f"Delete error: {e}")

        if self.delete_course_dialog:
            self.delete_course_dialog.dismiss()
