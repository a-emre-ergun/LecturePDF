from kivy.properties import StringProperty

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen


class ScheduleScreen(MDScreen):
    def on_fab_press(self):
        MDApp.get_running_app().show_add_schedule_dialog()


class ScheduleDetailScreen(MDScreen):
    schedule_name = StringProperty("Schedule Details")
    schedule_filename = StringProperty("")
