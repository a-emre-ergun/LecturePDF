import os

from src.utils.platform import is_android, is_ios

_FOLDER_PICK_REQUEST_CODE = 9001
_IMAGE_PICK_REQUEST_CODE = 9002


def pick_folder(title="Select Folder", on_selection=None):
    if is_android():
        _android_pick_folder(on_selection)
        return None
    if is_ios():
        _ios_pick_folder(on_selection)
        return None
    return _desktop_pick_folder(title, on_selection)


def pick_images(title="Select Photos", on_selection=None):
    if is_android():
        _android_pick_images(on_selection)
        return []
    if is_ios():
        _ios_pick_images(on_selection)
        return []
    return _desktop_pick_images(title, on_selection)


def _desktop_pick_folder(title, on_selection):
    from tkinter import filedialog, Tk

    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askdirectory(title=title)
    root.destroy()
    result = path if path else None
    if on_selection:
        on_selection(result)
    return result


def _desktop_pick_images(title, on_selection):
    from tkinter import filedialog, Tk

    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    files = filedialog.askopenfilenames(
        title=title,
        filetypes=[
            ("Image files", "*.jpg *.jpeg *.png *.JPG *.JPEG *.PNG")]
    )
    root.destroy()
    result = list(files) if files else []
    if on_selection:
        on_selection(result)
    return result


def _ios_pick_folder(on_selection):
    if on_selection:
        on_selection(None)


def _ios_pick_images(on_selection):
    if on_selection:
        on_selection([])


def _get_sdk_version():
    from jnius import autoclass
    Version = autoclass("android.os.Build$VERSION")
    return Version.SDK_INT


def _get_image_permissions():
    from android.permissions import Permission
    if _get_sdk_version() >= 33:
        return [Permission.READ_MEDIA_IMAGES]
    return [Permission.READ_EXTERNAL_STORAGE]


def _get_storage_permissions():
    from android.permissions import Permission
    if _get_sdk_version() >= 33:
        return [Permission.READ_MEDIA_IMAGES]
    return [Permission.READ_EXTERNAL_STORAGE]


def _android_request_permission(permissions, callback):
    from android.permissions import request_permissions, check_permission

    if all(check_permission(p) for p in permissions):
        callback(True)
        return

    def _on_result(perms, grants):
        callback(all(grants))

    request_permissions(permissions, _on_result)


def _android_pick_folder(on_selection):
    def _after_permission(granted):
        if not granted:
            if on_selection:
                on_selection(None)
            return
        _launch_native_folder_picker(on_selection)

    _android_request_permission(
        _get_storage_permissions(),
        _after_permission
    )


def _launch_native_folder_picker(on_selection):
    try:
        from jnius import autoclass
        from android.activity import bind as activity_bind, unbind as activity_unbind
    except ImportError:
        if on_selection:
            on_selection(None)
        return

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Intent = autoclass("android.content.Intent")
    activity = PythonActivity.mActivity

    def _on_activity_result(request_code, result_code, intent):
        if request_code != _FOLDER_PICK_REQUEST_CODE:
            return

        activity_unbind(on_activity_result=_on_activity_result)

        Activity = autoclass("android.app.Activity")
        if result_code != Activity.RESULT_OK or intent is None:
            if on_selection:
                on_selection(None)
            return

        uri = intent.getData()
        if uri is None:
            if on_selection:
                on_selection(None)
            return

        try:
            flags = (Intent.FLAG_GRANT_READ_URI_PERMISSION
                     | Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
            activity.getContentResolver().takePersistableUriPermission(uri, flags)
        except Exception:
            pass

        path = _resolve_tree_uri_to_path(uri)
        if on_selection:
            on_selection(path)

    activity_bind(on_activity_result=_on_activity_result)
    intent = Intent(Intent.ACTION_OPEN_DOCUMENT_TREE)
    activity.startActivityForResult(intent, _FOLDER_PICK_REQUEST_CODE)


def _resolve_tree_uri_to_path(uri):
    try:
        from jnius import autoclass
        DocumentsContract = autoclass("android.provider.DocumentsContract")
        doc_id = DocumentsContract.getTreeDocumentId(uri)

        parts = doc_id.split(":")
        storage_type = parts[0]
        relative_path = parts[1] if len(parts) > 1 else ""

        if storage_type == "primary":
            Environment = autoclass("android.os.Environment")
            root = str(Environment.getExternalStorageDirectory().getAbsolutePath())
            if relative_path:
                return os.path.join(root, relative_path)
            return root

        storage_path = os.path.join("/storage", storage_type)
        if relative_path:
            return os.path.join(storage_path, relative_path)
        return storage_path
    except Exception:
        return None


def _android_pick_images(on_selection):
    def _after_permission(granted):
        if not granted:
            if on_selection:
                on_selection([])
            return
        _launch_native_image_picker(on_selection)

    _android_request_permission(
        _get_image_permissions(),
        _after_permission
    )


def _launch_native_image_picker(on_selection):
    try:
        from jnius import autoclass
        from android.activity import bind as activity_bind, unbind as activity_unbind
    except ImportError:
        if on_selection:
            on_selection([])
        return

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Intent = autoclass("android.content.Intent")
    activity = PythonActivity.mActivity

    def _on_activity_result(request_code, result_code, intent):
        if request_code != _IMAGE_PICK_REQUEST_CODE:
            return

        activity_unbind(on_activity_result=_on_activity_result)

        Activity = autoclass("android.app.Activity")
        if result_code != Activity.RESULT_OK or intent is None:
            if on_selection:
                on_selection([])
            return

        uris = []
        clip_data = intent.getClipData()
        if clip_data is not None:
            for i in range(clip_data.getItemCount()):
                uris.append(clip_data.getItemAt(i).getUri())
        else:
            uri = intent.getData()
            if uri is not None:
                uris.append(uri)

        if not uris:
            if on_selection:
                on_selection([])
            return

        paths = []
        for uri in uris:
            path = _copy_uri_to_cache(activity, uri)
            if path:
                paths.append(path)

        if on_selection:
            on_selection(paths)

    activity_bind(on_activity_result=_on_activity_result)
    intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
    intent.addCategory(Intent.CATEGORY_OPENABLE)
    intent.setType("image/*")
    intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, True)
    activity.startActivityForResult(intent, _IMAGE_PICK_REQUEST_CODE)


def _copy_uri_to_cache(activity, uri):
    try:
        from jnius import autoclass

        resolver = activity.getContentResolver()
        filename = _get_filename_from_uri(resolver, uri)
        if not filename:
            filename = f"image_{abs(hash(uri.toString())) % 0xFFFFFFFF}.jpg"

        cache_dir = os.path.join(
            str(activity.getCacheDir().getAbsolutePath()), "picked_images"
        )
        os.makedirs(cache_dir, exist_ok=True)

        dest_path = os.path.join(cache_dir, filename)
        if os.path.exists(dest_path):
            name, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(dest_path):
                dest_path = os.path.join(cache_dir, f"{name}_{counter}{ext}")
                counter += 1

        pfd = resolver.openFileDescriptor(uri, "r")
        fd = pfd.detachFd()

        with os.fdopen(fd, "rb") as src, open(dest_path, "wb") as dst:
            while True:
                chunk = src.read(8192)
                if not chunk:
                    break
                dst.write(chunk)

        return dest_path
    except Exception as e:
        print(f"Error copying URI to cache: {e}")
        return None


def _get_filename_from_uri(resolver, uri):
    try:
        from jnius import autoclass

        cursor = resolver.query(uri, None, None, None, None)
        if cursor is not None and cursor.moveToFirst():
            OpenableColumns = autoclass("android.provider.OpenableColumns")
            name_index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
            if name_index >= 0:
                name = cursor.getString(name_index)
                cursor.close()
                return name
            cursor.close()
    except Exception:
        pass
    return None
