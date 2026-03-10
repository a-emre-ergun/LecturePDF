from tkinter import filedialog, Tk


def pick_folder(title="Select Folder"):
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askdirectory(title=title)
    root.destroy()
    return path if path else None


def pick_images(title="Select Photos"):
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    files = filedialog.askopenfilenames(
        title=title,
        filetypes=[
            ("Image files", "*.jpg *.jpeg *.png *.JPG *.JPEG *.PNG")]
    )
    root.destroy()
    return list(files) if files else []
