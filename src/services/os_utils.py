import os

from kivymd.app import MDApp

from src.utils.platform import is_android, is_ios, PLATFORM


def get_downloads_folder():
    if is_android():
        return _android_downloads_folder()
    if is_ios():
        return _ios_downloads_folder()
    return _desktop_downloads_folder()


def _desktop_downloads_folder():
    return os.path.join(os.path.expanduser("~"), "Downloads")


def _android_downloads_folder():
    try:
        from jnius import autoclass
        Environment = autoclass("android.os.Environment")
        downloads = Environment.getExternalStoragePublicDirectory(
            Environment.DIRECTORY_DOWNLOADS
        )
        path = str(downloads.getAbsolutePath())
        if os.access(path, os.W_OK):
            return path
    except Exception:
        pass
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        context = PythonActivity.mActivity
        return str(context.getExternalFilesDir(None).getAbsolutePath())
    except Exception:
        return "/sdcard/Download"


def _ios_downloads_folder():
    return os.path.join(os.path.expanduser("~"), "Documents")


def get_system_theme_style():
    if is_android():
        return _android_system_theme_style()
    if is_ios():
        return _ios_system_theme_style()
    return _desktop_system_theme_style()


def _desktop_system_theme_style():
    try:
        import darkdetect
        return darkdetect.theme()
    except Exception as e:
        print(f"Theme detection error: {e}")
        return "Light"


def _android_system_theme_style():
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        context = PythonActivity.mActivity
        Configuration = autoclass("android.content.res.Configuration")
        ui_mode = context.getResources().getConfiguration().uiMode
        night_mask = Configuration.UI_MODE_NIGHT_MASK
        is_dark = (ui_mode & night_mask) == Configuration.UI_MODE_NIGHT_YES
        return "Dark" if is_dark else "Light"
    except Exception as e:
        print(f"Android theme detection error: {e}")
        return "Light"


def _ios_system_theme_style():
    return "Light"


def open_pdf_file(filepath):
    if not os.path.exists(filepath):
        MDApp.get_running_app().show_missing_file_dialog(filepath)
        return

    try:
        if is_android():
            _android_open_pdf_file(filepath)
        elif is_ios():
            _ios_open_pdf_file(filepath)
        else:
            _desktop_open_pdf_file(filepath)
    except Exception as e:
        app = MDApp.get_running_app()
        print(f"Error opening PDF: {e}")
        app.show_snackbar(app._("Failed to open PDF."))


def _desktop_open_pdf_file(filepath):
    import subprocess
    if PLATFORM == "win32":
        os.startfile(filepath)
    elif PLATFORM == "linux":
        subprocess.Popen(["xdg-open", filepath])
    elif PLATFORM == "darwin":
        subprocess.Popen(["open", filepath])


def _android_open_pdf_file(filepath):
    _android_open_file(filepath, "application/pdf")


def _ios_open_pdf_file(filepath):
    pass


def open_file_location(filepath):
    app = MDApp.get_running_app()
    if not os.path.exists(filepath):
        app.show_snackbar(app._("PDF file not found!"))
        return

    try:
        if is_android():
            _android_open_file_location(filepath)
        elif is_ios():
            _ios_open_file_location(filepath)
        else:
            _desktop_open_file_location(filepath)
    except Exception as e:
        print(f"Error opening location: {e}")
        app.show_snackbar(app._("Failed to open folder location."))


def _desktop_open_file_location(filepath):
    import subprocess
    if PLATFORM == "win32":
        subprocess.run(
            ["explorer", "/select,", os.path.normpath(filepath)])
    elif PLATFORM == "linux":
        subprocess.Popen(["xdg-open", os.path.dirname(filepath)])
    elif PLATFORM == "darwin":
        subprocess.Popen(["open", "-R", filepath])


def _android_open_file_location(filepath):
    try:
        from jnius import autoclass

        Intent = autoclass("android.content.Intent")
        DownloadManager = autoclass("android.app.DownloadManager")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")

        context = PythonActivity.mActivity
        intent = Intent(DownloadManager.ACTION_VIEW_DOWNLOADS)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
    except Exception:
        pass


def _ios_open_file_location(filepath):
    pass


def _android_open_file(filepath, mime_type):
    from jnius import autoclass

    Intent = autoclass("android.content.Intent")
    File = autoclass("java.io.File")
    PythonActivity = autoclass("org.kivy.android.PythonActivity")

    context = PythonActivity.mActivity
    java_file = File(filepath)

    try:
        FileProvider = autoclass("androidx.core.content.FileProvider")
        package_name = context.getPackageName()
        uri = FileProvider.getUriForFile(
            context, f"{package_name}.fileprovider", java_file
        )
    except Exception:
        StrictMode = autoclass("android.os.StrictMode")
        VmPolicyBuilder = autoclass("android.os.StrictMode$VmPolicy$Builder")
        StrictMode.setVmPolicy(VmPolicyBuilder().build())
        Uri = autoclass("android.net.Uri")
        uri = Uri.fromFile(java_file)

    intent = Intent(Intent.ACTION_VIEW)
    intent.setDataAndType(uri, mime_type)
    intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    context.startActivity(intent)


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
        if is_android():
            return _android_pdf_thumbnail(pdf_path, thumb_path)
        if is_ios():
            return _ios_pdf_thumbnail(pdf_path, thumb_path)
        return _desktop_pdf_thumbnail(pdf_path, thumb_path)
    except Exception as e:
        print(f"Thumbnail error: {e}")
        return None


def _desktop_pdf_thumbnail(pdf_path, thumb_path):
    import fitz
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)
    pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
    pix.save(thumb_path)
    doc.close()
    return thumb_path


def _android_pdf_thumbnail(pdf_path, thumb_path):
    from jnius import autoclass

    PdfRenderer = autoclass("android.graphics.pdf.PdfRenderer")
    PdfRendererPage = autoclass("android.graphics.pdf.PdfRenderer$Page")
    ParcelFileDescriptor = autoclass("android.os.ParcelFileDescriptor")
    File = autoclass("java.io.File")
    Bitmap = autoclass("android.graphics.Bitmap")
    BitmapConfig = autoclass("android.graphics.Bitmap$Config")
    FileOutputStream = autoclass("java.io.FileOutputStream")
    CompressFormat = autoclass("android.graphics.Bitmap$CompressFormat")

    pfd = ParcelFileDescriptor.open(
        File(pdf_path), ParcelFileDescriptor.MODE_READ_ONLY
    )
    renderer = PdfRenderer(pfd)
    page = renderer.openPage(0)

    width = page.getWidth() // 2
    height = page.getHeight() // 2
    bitmap = Bitmap.createBitmap(width, height, BitmapConfig.ARGB_8888)
    page.render(
        bitmap, None, None, PdfRendererPage.RENDER_MODE_FOR_DISPLAY
    )

    fos = FileOutputStream(File(thumb_path))
    bitmap.compress(CompressFormat.PNG, 100, fos)
    fos.flush()
    fos.close()

    page.close()
    renderer.close()
    pfd.close()

    return thumb_path


def _ios_pdf_thumbnail(pdf_path, thumb_path):
    return None
