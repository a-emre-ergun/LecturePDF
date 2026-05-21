from kivy.clock import Clock

from kivymd.uix.screen import MDScreen


class HistoryScreen(MDScreen):
    def on_pre_enter(self):
        self.opacity = 0

    def on_enter(self):
        Clock.schedule_once(lambda dt: setattr(self, "opacity", 1), 0)
