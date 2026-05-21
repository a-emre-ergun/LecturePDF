from kivy.clock import Clock
from kivy.properties import StringProperty

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen


class ScheduleScreen(MDScreen):
    def on_fab_press(self):
        MDApp.get_running_app().show_add_schedule_dialog()


class ScheduleDetailScreen(MDScreen):
    schedule_name = StringProperty("Schedule Details")
    schedule_filename = StringProperty("")

    def on_pre_enter(self):
        self.opacity = 0

    def on_enter(self):
        Clock.schedule_once(lambda dt: setattr(self, "opacity", 1), 0)
