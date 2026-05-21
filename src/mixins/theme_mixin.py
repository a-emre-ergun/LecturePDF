import os

from kivy.clock import Clock
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemTrailingIcon

from src.services.os_utils import get_system_theme_style
from src.utils.platform import is_android, is_desktop


class ThemeMixin:
    def open_theme_menu(self, instance_item):
        theme_options = [
            (self._("System"), "system"),
            (self._("Light"), "light"),
            (self._("Dark"), "dark")
        ]

        menu_items = [
            {
                "text": name,
                "on_release": lambda x=name, c=code: self.set_theme_from_menu(x, c),
            } for name, code in theme_options
        ]

        self.theme_menu = MDDropdownMenu(
            caller=instance_item,
            items=menu_items,
            position="bottom",
            width_mult=3,
        )
        self.theme_menu.open()

    def set_theme_from_menu(self, theme_name, theme_code):
        self.theme_menu.dismiss()
        self.set_theme(theme_code)

    def set_theme(self, theme_code):
        self.save_setting("theme_mode", theme_code)
        self.apply_theme(theme_code)
        self.refresh_schedule_list_ui()

    def apply_theme(self, theme_code):
        if theme_code == "light":
            self.theme_cls.theme_style = "Light"
            self.current_theme_name = "Light"
        elif theme_code == "dark":
            self.theme_cls.theme_style = "Dark"
            self.current_theme_name = "Dark"
        else:
            detected_style = get_system_theme_style()
            self.theme_cls.theme_style = detected_style
            self.current_theme_name = "System"

    def open_palette_menu(self, instance_item):
        palettes = [("Blue", self._("Blue")),
                    ("Red", self._("Red")),
                    ("Green", self._("Green")),
                    ("Yellow", self._("Yellow"))
                    ]

        menu_items = [
            {
                "text": display_name,
                "on_release": lambda x=internal_name: self.set_palette_from_menu(x),
            } for internal_name, display_name in palettes
        ]

        self.palette_menu = MDDropdownMenu(
            caller=instance_item,
            items=menu_items,
            position="bottom",
        )

        self.palette_menu.open()

    def set_palette_from_menu(self, palette_name):
        self.palette_menu.dismiss()
        self.set_palette(palette_name)

    def set_palette(self, palette_name):
        self.current_palette_name = palette_name
        self.theme_cls.primary_palette = palette_name
        self.save_setting("color_palette", palette_name)
        self.refresh_schedule_list_ui()

    def toggle_dynamic_color(self, active):
        self.dynamic_color_enabled = active
        self.save_setting("dynamic_color", active)
        if active:
            self.apply_dynamic_color()
        else:
            saved_palette = self.get_setting("color_palette") or "Blue"
            self.set_palette(saved_palette)

    def apply_dynamic_color(self):
        if not is_android():
            self.dynamic_color_enabled = False
            self.save_setting("dynamic_color", False)
            return

        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            context = PythonActivity.mActivity

            WallpaperManager = autoclass("android.app.WallpaperManager")
            wm = WallpaperManager.getInstance(context)

            colors = wm.getWallpaperColors(WallpaperManager.FLAG_SYSTEM)
            if colors:
                primary_color_int = colors.getPrimaryColor().toArgb()
                r = (primary_color_int >> 16) & 0xFF
                g = (primary_color_int >> 8) & 0xFF
                b = primary_color_int & 0xFF
                self.theme_cls.primaryColor = [r / 255, g / 255, b / 255, 1]
                self.current_palette_name = self._("Dynamic Color")
        except Exception as e:
            print(f"Dynamic color error: {e}")
            self.dynamic_color_enabled = False
            self.save_setting("dynamic_color", False)

    def open_language_screen(self):
        self.load_language_list()

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
        Clock.schedule_once(lambda dt: setattr(sm, "current", "LanguageScreen"), 0)

    def go_back_to_settings(self):
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

        Clock.schedule_once(lambda dt: setattr(sm, "current", "Settings"), 0)

    def load_language_list(self):
        screen = self.root.ids.screen_manager.get_screen("LanguageScreen")
        list_container = screen.ids.language_list
        list_container.clear_widgets()

        saved_lang = self.get_setting("language")
        if not saved_lang or (saved_lang != "system" and saved_lang not in self.available_languages):
            saved_lang = "en"

        system_item = MDListItem(
            on_release=lambda x: self.select_language_and_go_back(
                "system", self._("System Language"))
        )
        system_item.add_widget(
            MDListItemHeadlineText(text=self._("System Language")))
        if saved_lang == "system":
            system_item.add_widget(
                MDListItemTrailingIcon(
                    icon="check-circle",
                    theme_icon_color="Custom",
                    icon_color=self.theme_cls.primaryColor
                )
            )
        list_container.add_widget(system_item)

        for lang_code, lang_name in self.available_languages.items():
            item = MDListItem(
                on_release=lambda x, lc=lang_code, ln=lang_name: self.select_language_and_go_back(
                    lc, ln)
            )
            item.add_widget(MDListItemHeadlineText(text=lang_name))

            if lang_code == saved_lang:
                item.add_widget(
                    MDListItemTrailingIcon(
                        icon="check-circle",
                        theme_icon_color="Custom",
                        icon_color=self.theme_cls.primaryColor
                    )
                )

            list_container.add_widget(item)

    def select_language_and_go_back(self, lang_code, lang_name):
        resolved = self._resolve_language(lang_code)

        if self.tr:
            self.tr.switch_language(resolved)

        self.save_setting("language", lang_code)
        if lang_code == "system":
            self.current_language_name = self._("System Language")
        else:
            self.current_language_name = lang_name

        self.refresh_schedule_list_ui()

        if hasattr(self.root.ids, "top_app_bar_title"):
            self.root.ids.top_app_bar_title.text = self._("Settings")

        self.refresh_create_screen_texts()
        self._refresh_naming_format_name()

        self.go_back_to_settings()
