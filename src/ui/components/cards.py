from kivy.properties import StringProperty, BooleanProperty

from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.navigationbar import MDNavigationItem


class PDFHistoryCard(MDCard):
    filename = StringProperty()
    filepath = StringProperty()
    thumbnail = StringProperty(allownone=True)
    course = StringProperty()
    schedule = StringProperty()
    week = StringProperty()
    date = StringProperty()
    is_missing = BooleanProperty(False)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if "button" in touch.profile:
                if touch.button == "right":
                    MDApp.get_running_app().on_card_right_click(self, touch, self.filepath)
                    return True
                elif touch.button not in ("left", "scrollup", "scrolldown"):
                    return True
        return super().on_touch_down(touch)


class BaseMDNavigationItem(MDNavigationItem):
    icon = StringProperty()
    text = StringProperty()
