from kivy.clock import Clock

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import (
    MDListItem, MDListItemLeadingIcon,
    MDListItemHeadlineText, MDListItemSupportingText
)
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton


class NamingFormatScreen(MDScreen):
    def on_pre_enter(self):
        self.opacity = 0

    def on_enter(self):
        Clock.schedule_once(lambda dt: setattr(self, "opacity", 1), 0)

    def load_formats(self):
        app = MDApp.get_running_app()
        formats = app._get_naming_formats()
        container = self.ids.naming_format_list
        container.clear_widgets()

        for index, fmt in enumerate(formats):
            item = MDListItem(
                on_release=lambda x, i=index: app.set_active_naming_format(i)
            )

            if fmt.get("is_active"):
                item.add_widget(
                    MDListItemLeadingIcon(
                        icon="check-circle",
                        theme_icon_color="Custom",
                        icon_color=app.theme_cls.primaryColor
                    )
                )
            else:
                item.add_widget(
                    MDListItemLeadingIcon(
                        icon="circle-outline",
                        theme_icon_color="Custom",
                        icon_color=app.theme_cls.onSurfaceVariantColor
                    )
                )

            display_name = app._(fmt["name"]) if fmt.get("is_preset") else fmt["name"]
            item.add_widget(MDListItemHeadlineText(text=display_name))
            item.add_widget(
                MDListItemSupportingText(text=fmt["format_string"])
            )

            if not fmt.get("is_preset"):
                trailing_box = MDBoxLayout(
                    adaptive_size=True,
                    pos_hint={"center_y": .5},
                )

                edit_btn = MDIconButton(
                    icon="pencil-outline",
                    style="standard",
                    theme_icon_color="Custom",
                    icon_color=app.theme_cls.primaryColor,
                )
                edit_btn.bind(
                    on_release=lambda x, i=index: app.show_edit_naming_format_dialog(i)
                )

                delete_btn = MDIconButton(
                    icon="trash-can-outline",
                    style="standard",
                    theme_icon_color="Custom",
                    icon_color=[0.91, 0.05, 0.21, 1],
                )
                delete_btn.bind(
                    on_release=lambda x, i=index: app.confirm_delete_naming_format(i)
                )

                trailing_box.add_widget(edit_btn)
                trailing_box.add_widget(delete_btn)
                item.add_widget(trailing_box)

            container.add_widget(item)
