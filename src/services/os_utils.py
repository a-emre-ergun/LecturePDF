import os
import subprocess
import sys
from pathlib import Path

import fitz
from kivymd.app import MDApp


def get_downloads_folder():
    return str(Path.home() / "Downloads")


def get_system_theme_style():
    try:
        import darkdetect
        return darkdetect.theme()
    except Exception as e:
        print(f"Theme detection error: {e}")
        return "Light"


def open_pdf_file(filepath):
    if not os.path.exists(filepath):
        MDApp.get_running_app().show_missing_file_dialog(filepath)
        return

    try:
        if sys.platform == "win32":
            os.startfile(filepath)
        elif sys.platform == "linux":
            subprocess.Popen(["xdg-open", filepath])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", filepath])
        else:
            raise OSError(f"Unsupported platform: {sys.platform}")
    except Exception as e:
        app = MDApp.get_running_app()
        print(f"Error opening PDF: {e}")
        app.show_snackbar(app._("Failed to open PDF."))


def open_file_location(filepath):
    app = MDApp.get_running_app()
    if not os.path.exists(filepath):
        app.show_snackbar(app._("PDF file not found!"))
        return
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["explorer", "/select,", os.path.normpath(filepath)])
        elif sys.platform == "linux":
            subprocess.Popen(["xdg-open", os.path.dirname(filepath)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", filepath])
        else:
            raise OSError(f"Unsupported platform: {sys.platform}")
    except Exception as e:
        print(f"Error opening location: {e}")
        app.show_snackbar(app._("Failed to open folder location."))


def get_pdf_thumbnail(pdf_path, thumbnail_dir):
    if not os.path.exists(pdf_path):
        return None

    parent_folder = os.path.basename(os.path.dirname(pdf_path))
    filename = os.path.basename(pdf_path)
    thumb_name = f"{parent_folder}_{filename}.png"
    thumb_path = os.path.join(thumbnail_dir, thumb_name)

    if os.path.exists(thumb_path):
        return thumb_path

    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(
            0.5, 0.5))
        pix.save(thumb_path)
        doc.close()
        return thumb_path
    except Exception as e:
        print(f"Thumbnail error: {e}")
        return None
