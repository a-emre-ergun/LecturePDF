import os

from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemTrailingIcon

from src.services.os_utils import get_system_theme_style


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

    def open_language_screen(self):
        self.load_language_list()
        self.root.ids.screen_manager.current = "LanguageScreen"

        gb = self.root.ids.global_app_bar
        gb.opacity = 0
        gb.disabled = True
        gb.height = 0

        nb = self.root.ids.nav_bar
        nb.opacity = 0
        nb.disabled = True
        nb.height = 0

    def go_back_to_settings(self):
        self.root.ids.screen_manager.current = "Settings"

        gb = self.root.ids.global_app_bar
        gb.opacity = 1
        gb.disabled = False
        gb.height = "64dp"

        nb = self.root.ids.nav_bar
        nb.opacity = 1
        nb.disabled = False
        nb.height = "80dp"

    def load_language_list(self):
        screen = self.root.ids.screen_manager.get_screen("LanguageScreen")
        list_container = screen.ids.language_list
        list_container.clear_widgets()

        saved_lang = self.get_setting("language")
        if not saved_lang or saved_lang not in self.available_languages:
            saved_lang = "en"

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
        if self.tr:
            self.tr.switch_language(lang_code)

        self.save_setting("language", lang_code)
        self.current_language_name = lang_name

        self.refresh_schedule_list_ui()

        if hasattr(self.root.ids, "top_app_bar_title"):
            self.root.ids.top_app_bar_title.text = self._("Settings")

        self.refresh_create_screen_texts()

        self.go_back_to_settings()
