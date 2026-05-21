from kivy.core.window import Window
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Line, Rectangle, StencilPush, StencilUse, StencilUnUse, StencilPop

from kivymd.app import MDApp
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.label import MDLabel

from src.utils.platform import is_android


class TutorialOverlay(MDFloatLayout):
    def __init__(self, steps, **kwargs):
        super().__init__(**kwargs)
        self.steps = steps
        self.current_step = 0
        self.size_hint = (1, 1)
        self.pos_hint = {"x": 0, "y": 0}
        self.show_step()

    def show_step(self):
        self.clear_widgets()
        self.canvas.before.clear()
        self.canvas.after.clear()

        if self.current_step >= len(self.steps):
            if self.parent:
                self.parent.remove_widget(self)

            MDApp.get_running_app().save_setting("tutorial_completed", True)
            return

        target_widget, title, desc = self.steps[self.current_step]

        abs_pos = target_widget.to_window(target_widget.x, target_widget.y)
        size = target_widget.size

        pad = dp(8)
        rect_pos = (abs_pos[0] - pad, abs_pos[1] - pad)
        rect_size = (size[0] + pad*2, size[1] + pad*2)
        radius = [dp(12),]

        with self.canvas.before:
            StencilPush()
            RoundedRectangle(pos=rect_pos, size=rect_size, radius=radius)
            StencilUse(op="notequal")
            Color(0, 0, 0, 0.85)
            Rectangle(pos=(0, 0), size=Window.size)
            StencilUnUse()
            StencilPop()

        with self.canvas.after:
            Color(1, 1, 1, 1)
            Line(rounded_rectangle=(
                rect_pos[0], rect_pos[1], rect_size[0], rect_size[1], radius[0]), width=1.5)

        text_pos_y = .75 if abs_pos[1] < Window.height / 2 else .25

        app = MDApp.get_running_app()
        if is_android():
            continue_text = app.tr._("Tap anywhere to continue...")
        else:
            continue_text = app.tr._("Click anywhere to continue...")

        info_label = MDLabel(
            text=f"[b][size=20sp]{title}[/size][/b]\n\n{desc}\n\n[i][size=13sp]{continue_text}[/size][/i]",
            markup=True,
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            pos_hint={"center_x": .5, "center_y": text_pos_y},
            size_hint_x=0.85,
            adaptive_height=True
        )
        self.add_widget(info_label)

    def on_touch_down(self, touch):
        return True

    def on_touch_up(self, touch):
        self.current_step += 1
        self.show_step()
        return True
