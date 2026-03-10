from kivy.config import Config
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.behaviors.ripple_behavior import CommonRipple


original_btn_touch_down = ButtonBehavior.on_touch_down
original_ripple_touch_down = CommonRipple.on_touch_down


def custom_btn_touch_down(self, touch):
    if "button" in touch.profile and touch.button not in ("left", "scrollup", "scrolldown"):
        return False
    return original_btn_touch_down(self, touch)


def custom_ripple_touch_down(self, touch):
    if "button" in touch.profile and touch.button not in ("left", "scrollup", "scrolldown"):
        return False
    return original_ripple_touch_down(self, touch)


def apply_touch_fixes():
    Config.set("input", "mouse", "mouse,disable_multitouch")
    ButtonBehavior.on_touch_down = custom_btn_touch_down
    CommonRipple.on_touch_down = custom_ripple_touch_down
