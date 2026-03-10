import os
import re
import threading
from datetime import datetime

from kivy.clock import Clock

from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogContentContainer
from kivymd.uix.label import MDLabel

from src.core.pdf_engine import LecturePDF
from src.services.os_utils import get_downloads_folder


class PDFGenerationMixin:
    def generate_pdfs(self):
        if self.is_generating_process_active:
            return

        active_schedule = next(
            (s for s in self.schedules if s["active"]), None)
        if not active_schedule:
            self.show_snackbar(self._("No active schedule found!"))
            return

        start_date_str = self.get_setting("semester_start")
        if not start_date_str:
            self.show_snackbar(self._("Please select a semester start date!"))
            return

        try:
            semester_start_date = datetime.strptime(start_date_str, "%d.%m.%Y")
        except ValueError:
            self.show_snackbar(self._("Invalid date format in settings!"))
            return

        create_screen = self.root.ids.screen_manager.get_screen("Create PDFs")
        folder_path = create_screen.selected_folder_path
        images_list = create_screen.selected_images_list

        if not folder_path and not images_list:
            self.show_snackbar(self._("Please select a folder or photos!"))
            return

        files_to_process = []
        if folder_path:
            try:
                for f in os.listdir(folder_path):
                    full_path = os.path.join(folder_path, f)
                    if os.path.isfile(full_path):
                        files_to_process.append(full_path)
            except Exception as e:
                print(f"Error reading folder: {e}")
                return
        else:
            files_to_process = images_list

        if not files_to_process:
            self.show_snackbar(self._("No files found to process!"))
            return

        base_folder = self.custom_output_path if self.custom_output_path else get_downloads_folder()

        self.loading_dialog = MDDialog(
            MDDialogHeadlineText(text=self._("Generating PDFs...")),
            MDDialogContentContainer(
                MDLabel(
                    text=self._("Please wait, analyzing photos and creating documents.")),
                orientation="vertical"
            ),
        )
        self.loading_dialog.auto_dismiss = False
        self.loading_dialog.open()

        schedule_full_path = os.path.join(
            self.project_root, active_schedule["filename"])

        raw_name = active_schedule["name"]
        safe_schedule_name = re.sub(
            r"[^\w\s-]", "", raw_name).strip().replace(" ", "_")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        folder_name = f"{safe_schedule_name}_{timestamp}"

        output_dir = os.path.join(base_folder, "LecturePDF", folder_name)

        self.is_generating_process_active = True

        threading.Thread(
            target=self._run_pdf_generation_thread,
            args=(schedule_full_path, semester_start_date,
                  files_to_process, output_dir),
            daemon=True
        ).start()

    def _run_pdf_generation_thread(self, schedule_path, start_date, file_list, output_dir):
        is_success = False
        try:
            processor = LecturePDF(verbose=True)

            processor.set_schedule(schedule_path)

            exif_data = processor.extract_photos_w_exif(file_list)

            organized_data = processor.organize_photos(exif_data, start_date)

            if not organized_data:
                msg = self._("No matching lectures found for these photos.")
            else:
                active_schedule_name = next(
                    (s["name"] for s in self.schedules if s["active"]), "Unknown")
                created_files = processor.create_pdfs(
                    organized_data, output_dir, db=self.db,
                    schedule_name=active_schedule_name)
                count = len(created_files)
                if count > 0:
                    msg = self._("Success! {count} PDFs are created").format(
                        count=count)
                    is_success = True
                else:
                    msg = self._("No PDFs created (check dates/times).")

        except ValueError as e:
            msg = str(e)

        except Exception as e:
            msg = self._(
                "An unexpected error occurred: {error}").format(error=e)
            print(e)

        Clock.schedule_once(
            lambda dt: self._on_pdf_generation_complete(msg, is_success))

    def _on_pdf_generation_complete(self, message, status=False):
        self.is_generating_process_active = False

        if hasattr(self, "loading_dialog"):
            self.loading_dialog.dismiss()

        self.show_snackbar(message)

        if status:
            create_screen = self.root.ids.screen_manager.get_screen(
                "Create PDFs")
            create_screen.clear_selection("folder")
            create_screen.clear_selection("image")
