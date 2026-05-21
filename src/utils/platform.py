import os
import sys


def _detect_platform():
    try:
        import android
        return "android"
    except ImportError:
        return sys.platform


PLATFORM = _detect_platform()


def is_android():
    return PLATFORM == "android"


def is_ios():
    return PLATFORM == "ios"


def is_desktop():
    return PLATFORM in ("win32", "darwin", "linux")


def get_bundle_dir():
    if is_android():
        return _android_bundle_dir()
    if is_ios():
        return _ios_bundle_dir()
    return _desktop_bundle_dir()


def _desktop_bundle_dir():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _android_bundle_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _ios_bundle_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_app_data_dir():
    if is_android():
        return _android_app_data_dir()
    if is_ios():
        return _ios_app_data_dir()
    return _desktop_app_data_dir()


def _desktop_app_data_dir():
    if getattr(sys, "frozen", False):
        if PLATFORM == "win32":
            base = os.environ.get("APPDATA", os.path.expanduser("~"))
        elif PLATFORM == "darwin":
            base = os.path.join(
                os.path.expanduser("~"), "Library", "Application Support")
        elif PLATFORM == "linux":
            base = os.environ.get("XDG_DATA_HOME", os.path.join(
                os.path.expanduser("~"), ".local", "share"))
        else:
            raise OSError(f"Unsupported desktop platform: {PLATFORM}")
        return os.path.join(base, "LecturePDF")
    return os.path.dirname(get_bundle_dir())


def _android_app_data_dir():
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        context = PythonActivity.mActivity
        return str(context.getFilesDir().getAbsolutePath())
    except Exception:
        return os.path.dirname(get_bundle_dir())


def _ios_app_data_dir():
    return os.path.dirname(get_bundle_dir())


def get_system_locale():
    if is_android():
        try:
            from jnius import autoclass
            Locale = autoclass("java.util.Locale")
            return Locale.getDefault().getLanguage()
        except Exception:
            return "en"

    import locale
    try:
        lang = locale.getdefaultlocale()[0]
        return lang.split("_")[0] if lang else "en"
    except Exception:
        return "en"
