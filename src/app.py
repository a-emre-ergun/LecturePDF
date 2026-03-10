import json
import os
import sys

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.screenmanager import NoTransition
from kivy.metrics import dp

from kivymd.app import MDApp
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText

from src.utils.i18n import Language
from src.utils.touch_fixes import apply_touch_fixes
from src.core.database import DatabaseManager
from src.ui.components.overlays import TutorialOverlay
from src.config import (
    COLOR_PALETTE, DAYS_MAP, DAYS_ABBR_LIST,
    DAY_STR_TO_INT, DAY_INT_TO_STR, AVAILABLE_LANGUAGES
)

from src.mixins.schedule_mixin import ScheduleMixin
from src.mixins.course_mixin import CourseMixin
from src.mixins.history_mixin import HistoryMixin
from src.mixins.pdf_mixin import PDFGenerationMixin
from src.mixins.theme_mixin import ThemeMixin

# These imports are needed so KV file can reference the classes
from src.ui.screens.create_pdfs import CreatePDFsScreen  # noqa: F401
from src.ui.screens.history import HistoryScreen  # noqa: F401
from src.ui.screens.schedules import ScheduleScreen, ScheduleDetailScreen  # noqa: F401
from src.ui.screens.settings import SettingsScreen, LanguageScreen  # noqa: F401
from src.ui.components.cards import PDFHistoryCard, BaseMDNavigationItem  # noqa: F401


apply_touch_fixes()


class App(ScheduleMixin, CourseMixin, HistoryMixin, PDFGenerationMixin, ThemeMixin, MDApp):
    current_theme_name = StringProperty("System")
    current_palette_name = StringProperty("Blue")
    current_language_name = StringProperty("English")
    palette_menu = ObjectProperty(None, allownone=True)
    custom_output_path = StringProperty("")
    tr = ObjectProperty(None, allownone=True)
    history_view_mode = StringProperty("list")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if getattr(sys, 'frozen', False):
            self.bundle_dir = sys._MEIPASS
            if sys.platform == "win32":
                base = os.environ.get("APPDATA", os.path.expanduser("~"))
            elif sys.platform == "darwin":
                base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
            elif sys.platform == "linux":
                base = os.environ.get("XDG_DATA_HOME", os.path.join(os.path.expanduser("~"), ".local", "share"))
            else:
                raise OSError(f"Unsupported platform: {sys.platform}")
            self.app_data_dir = os.path.join(base, "LecturePDF")
        else:
            self.bundle_dir = os.path.dirname(os.path.abspath(__file__))
            self.app_data_dir = os.path.dirname(self.bundle_dir)

        self.project_root = self.app_data_dir
        os.makedirs(self.app_data_dir, exist_ok=True)

        self.index_file = os.path.join(self.app_data_dir, "schedules_index.json")
        self.settings_file = os.path.join(self.app_data_dir, "settings.json")
        self.dialog = None
        self.course_dialog = None
        self.color_picker_dialog = None
        self.day_picker_dialog = None
        self.delete_course_dialog = None
        self.schedules = []
        self.past_courses_map = {}
        self.current_snackbar = None
        self.past_courses = []
        self.is_generating_process_active = False
        saved_view = self.get_setting("history_view_mode")
        self.history_view_mode = saved_view if saved_view else "list"
        self.thumbnail_dir = os.path.join(self.app_data_dir, ".thumbnails")
        self.available_languages = AVAILABLE_LANGUAGES
        os.makedirs(self.thumbnail_dir, exist_ok=True)

        self.color_palette = COLOR_PALETTE
        self.selected_color_hex = "039BE5"
        self.selected_day = None
        self.start_time = None
        self.end_time = None

        self.days_map = DAYS_MAP
        self.days_abbr_list = DAYS_ABBR_LIST

        self.day_str_to_int = DAY_STR_TO_INT
        self.day_int_to_str = DAY_INT_TO_STR

        self.db_path = os.path.join(self.app_data_dir, "pdfs.db")
        self.db = DatabaseManager(self.db_path)

    def build(self):
        saved_lang = self.get_setting("language")
        if not saved_lang:
            saved_lang = "en"
            self.save_setting("language", "en")

        self.title = "LecturePDF"

        self._ = lambda x: x
        self.tr = None

        try:
            assets_path = os.path.join(self.bundle_dir, "assets")
            self.tr = Language(saved_lang, language_path=assets_path)
            self._ = self.tr._
        except Exception as e:
            print(f"Error: {e}")
            self._ = lambda x: x
        self._ = self.tr._

        kv_path = os.path.join(self.bundle_dir, "src", "ui", "kv", "main.kv")
        if not os.path.exists(kv_path):
            kv_path = os.path.join(os.path.dirname(__file__), "ui", "kv", "main.kv")
        screen = Builder.load_file(kv_path)
        screen.ids.screen_manager.transition = NoTransition()

        return screen

    def change_language(self):
        if not self.tr:
            return

        current = self.tr.language
        new_lang = "en" if current == "tr" else "tr"

        self.tr.switch_language(new_lang)
        self.save_setting("language", new_lang)

        self.tr.switch_language(new_lang)
        self.save_setting("language", new_lang)

    def on_start(self):
        if sys.platform == "win32":
            icon_name = "icon.ico"
        elif sys.platform in ("linux", "darwin"):
            icon_name = "icon.png"
        else:
            icon_name = "icon.png"

        icon_path = os.path.join(self.bundle_dir, "assets", icon_name)
        if not os.path.exists(icon_path):
            icon_path = os.path.join(os.path.dirname(self.bundle_dir), "assets", icon_name)

        if os.path.exists(icon_path):
            if icon_name.endswith(".ico"):
                try:
                    from PIL import Image
                    import tempfile
                    img = Image.open(icon_path)
                    png_path = os.path.join(tempfile.gettempdir(), "lecturepdf_icon.png")
                    img.save(png_path, format="PNG")
                    self.icon = png_path
                    Window.set_icon(png_path)
                except Exception:
                    self.icon = icon_path
            else:
                self.icon = icon_path
                Window.set_icon(icon_path)

        saved_theme = self.get_setting("theme_mode")
        if not saved_theme:
            saved_theme = "system"
        self.apply_theme(saved_theme)

        saved_palette = self.get_setting("color_palette")
        if not saved_palette:
            saved_palette = "Blue"
        self.set_palette(saved_palette)

        self.load_schedule_index()
        self.refresh_schedule_list_ui()

        saved_output = self.get_setting("output_folder")
        if saved_output:
            self.custom_output_path = saved_output

        is_tutorial_done = self.get_setting("tutorial_completed")

        if not is_tutorial_done:
            Clock.schedule_once(self.start_tutorial, 1)

        saved_lang = self.get_setting("language")

        if not saved_lang or saved_lang not in self.available_languages:
            saved_lang = "en"
            self.save_setting("language", "en")

        self.current_language_name = self.available_languages[saved_lang]

        if self.tr:
            self.tr.switch_language(saved_lang)

        Window.bind(on_drop_file=self.on_file_drop)

        self.refresh_create_screen_texts()

    def on_file_drop(self, window, file_path, x, y):
        if self.root.ids.screen_manager.current != "Create PDFs":
            return

        try:
            decoded_path = file_path.decode("utf-8")
        except Exception as e:
            print(f"File drop error: {e}")
            return

        create_screen = self.root.ids.screen_manager.get_screen("Create PDFs")

        if os.path.isdir(decoded_path):
            if create_screen.selected_images_list:
                self.show_snackbar(
                    self._("Photos already selected! Clear them first."))
                return

            create_screen.selected_folder_path = decoded_path
            folder_name = os.path.basename(decoded_path)
            create_screen.ids.btn_folder_text.text = folder_name
            create_screen.ids.btn_clear_folder.opacity = 1
            create_screen.ids.btn_clear_folder.disabled = False
            return

        supported_formats = (".png", ".jpg", ".jpeg")
        if decoded_path.lower().endswith(supported_formats):
            if create_screen.selected_folder_path:
                self.show_snackbar(
                    self._("Folder already selected! Clear it first."))
                return

            current_list = list(create_screen.selected_images_list)
            if decoded_path not in current_list:
                current_list.append(decoded_path)
            create_screen.selected_images_list = current_list

            count = len(create_screen.selected_images_list)
            photos_selected_lbl = self._("Photos Selected")
            create_screen.ids.btn_photo_text.text = f"{count} {photos_selected_lbl}"
            create_screen.ids.btn_clear_photos.opacity = 1
            create_screen.ids.btn_clear_photos.disabled = False

    def start_tutorial(self, dt):
        screen = self.root.ids.screen_manager.get_screen("Create PDFs")
        self.root.ids.screen_manager.current = "Create PDFs"

        self.root.ids.top_app_bar_title.text = self._("LecturePDF")
        self.root.ids.nav_item_create.active = True
        self.root.ids.nav_item_schedules.active = False
        self.root.ids.nav_item_settings.active = False

        self.root.ids.history_btn_container.opacity = 1
        self.root.ids.history_btn.disabled = False

        for widget in self.root.children:
            if isinstance(widget, TutorialOverlay):
                self.root.remove_widget(widget)

        steps = [
            (screen.ids.btn_date_step,
             self._("Step 1: Select Date"),
             self._("Select semester start date from here.")),

            (screen.ids.btn_folder_step,
             self._("Step 2: Select Folder"),
             self._("Select a folder where your photos are...")),

            (screen.ids.btn_photo_step,
             self._("...Or Photos"),
             self._("...Or select photos one by one.")),

            (screen.ids.btn_generate_step,
             self._("Step 3: Create PDF"),
             self._("If everything is ready, click here and create PDFs!")),

            (self.root.ids.history_btn,
             self._("PDF History"),
             self._("Click here to view your previously generated PDFs.")),

            (self.root.ids.nav_item_schedules,
             self._("Schedules"),
             self._("Click here to add schedules.")),

            (self.root.ids.nav_item_settings,
             self._("Settings"),
             self._("Click here to change output folder."))
        ]

        overlay = TutorialOverlay(steps)
        self.root.add_widget(overlay)

    def save_setting(self, key, value):
        data = {}
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    data = json.load(f)
            except:
                data = {}

        data[key] = value

        with open(self.settings_file, "w") as f:
            json.dump(data, f)

    def get_setting(self, key):
        if not os.path.exists(self.settings_file):
            return None
        try:
            with open(self.settings_file, "r") as f:
                data = json.load(f)
            return data.get(key)
        except:
            return None

    def toggle_fab(self, show):
        fab = self.root.ids.fab
        fab.opacity = 1 if show else 0
        fab.disabled = not show

    def on_switch_tabs(self, bar, item, item_icon, item_text):
        target_screen = ""

        if item_icon == "file-document":
            self.root.ids.screen_manager.current = "Create PDFs"
            self.root.ids.top_app_bar_title.text = self._("LecturePDF")
            self.root.ids.fab.opacity = 0
            self.root.ids.fab.disabled = True
            self.root.ids.history_btn_container.opacity = 1
            self.root.ids.history_btn.disabled = False

        elif item_icon == "calendar-month":
            self.root.ids.screen_manager.current = "Schedules"
            self.root.ids.top_app_bar_title.text = self._("Schedules")
            self.root.ids.fab.opacity = 1
            self.root.ids.fab.disabled = False
            self.root.ids.history_btn_container.opacity = 0
            self.root.ids.history_btn.disabled = True

        elif item_icon == "cog":
            self.root.ids.screen_manager.current = "Settings"
            self.root.ids.top_app_bar_title.text = self._("Settings")
            self.root.ids.fab.opacity = 0
            self.root.ids.fab.disabled = True
            self.root.ids.history_btn_container.opacity = 0
            self.root.ids.history_btn.disabled = True

        if target_screen:
            self.root.ids.screen_manager.current = target_screen

    def on_fab_press(self):
        current_screen = self.root.ids.screen_manager.current_screen
        if hasattr(current_screen, "on_fab_press"):
            current_screen.on_fab_press()

    def show_snackbar(self, message):
        if self.current_snackbar:
            self.current_snackbar.dismiss()

        self.current_snackbar = MDSnackbar(
            MDSnackbarText(text=message),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.8,
        )
        self.current_snackbar.open()

    def refresh_create_screen_texts(self):
        create_screen = self.root.ids.screen_manager.get_screen("Create PDFs")

        saved_start_date = self.get_setting("semester_start")
        if saved_start_date:
            lbl = self._("Start Date")
            create_screen.ids.btn_date_text.text = f"{lbl}: {saved_start_date}"

        if create_screen.selected_folder_path:
            create_screen.ids.btn_folder_text.text = os.path.basename(
                create_screen.selected_folder_path)

        count = len(create_screen.selected_images_list)
        if count > 0:
            photos_selected_lbl = self._("Photos Selected")
            create_screen.ids.btn_photo_text.text = f"{count} {photos_selected_lbl}"

    def translate_date_picker(self, widget, clock_ev=None):
        if not hasattr(widget, "_headers_translated"):
            widget._headers_translated = False

        calendar_keys = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
            "Jan", "Feb", "Mar", "Apr", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
            "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
            "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "mm/dd/yyyy", "Select date"
        ]

        t_count = 0
        s_count = 0
        headers_count = 0

        for child in widget.walk():
            if hasattr(child, "text") and child.text:
                original = child.text.strip()

                if not widget._headers_translated and len(original) == 1 and original in "MTWTFSS":
                    key = f"initial_{original}"
                    if original == "T":
                        t_count += 1
                        key = f"initial_T{t_count}"
                    elif original == "S":
                        s_count += 1
                        key = f"initial_S{s_count}"

                    translated = self.tr._(key)
                    if translated != key:
                        child.text = translated
                        headers_count += 1
                elif len(original) > 1:
                    new_text = original
                    for k in sorted(calendar_keys, key=len, reverse=True):
                        if k in new_text:
                            translated_val = self.tr._(k)
                            if translated_val != k:
                                new_text = new_text.replace(k, translated_val)

                    if new_text != original:
                        child.text = new_text

        if headers_count >= 7:
            widget._headers_translated = True

    def _translation_hints():
        def _(x): return x
        _("Monday")
        _("Tuesday")
        _("Wednesday")
        _("Thursday")
        _("Friday")
        _("Saturday")
        _("Sunday")

        _("Mon")
        _("Tue")
        _("Wed")
        _("Thu")
        _("Fri")
        _("Sat")
        _("Sun")

        _("Select Semester Start Date")
        _("Select Input Folder")
        _("Select Photos")
        _("GENERATE PDF")
        _("Theme")
        _("Dynamic Color")
        _("Use system color")
        _("LecturePDF")
        _("Create PDFs")
        _("Schedules")
        _("Settings")
        _("Show Tutorial")
        _("Show Initial Tutorial")
        _("Blue")
        _("Red")
        _("Green")
        _("Yellow")
        _("Default (Downloads)")
        _("Language")
        _("Search by file name...")
        _("Color Palette")
        _("Jan")
        _("Feb")
        _("Mar")
        _("Apr")
        _("May")
        _("Jun")
        _("Jul")
        _("Aug")
        _("Sep")
        _("Oct")
        _("Nov")
        _("Dec")
        _("Ok")
        _("Cancel")
        _("January")
        _("February")
        _("March")
        _("April")
        _("May")
        _("June")
        _("July")
        _("August")
        _("September")
        _("October")
        _("November")
        _("December")
        _("initial_M")
        _("initial_T1")
        _("initial_W")
        _("initial_T2")
        _("initial_F")
        _("initial_S1")
        _("initial_S2")
        _("mm/dd/yyyy")
        _("File missing!")
