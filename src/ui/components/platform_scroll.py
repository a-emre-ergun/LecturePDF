from kivy.uix.scrollview import ScrollView
from kivy.uix.recycleview import RecycleView
from kivy.effects.scroll import ScrollEffect
from kivy.effects.dampedscroll import DampedScrollEffect
from kivy.metrics import dp

from src.utils.platform import is_desktop


class PlatformScrollView(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if is_desktop():
            self.scroll_type = ["bars"]
            self.effect_cls = ScrollEffect
            self.bar_width = dp(4)
        else:
            self.scroll_type = ["content"]
            self.effect_cls = DampedScrollEffect


class PlatformRecycleView(RecycleView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if is_desktop():
            self.scroll_type = ["bars"]
            self.effect_cls = ScrollEffect
            self.bar_width = dp(4)
        else:
            self.scroll_type = ["content"]
            self.effect_cls = DampedScrollEffect
