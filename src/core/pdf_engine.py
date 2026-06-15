import os
import re
import json
from datetime import datetime

from PIL import Image, ImageOps
from fpdf import FPDF
from pillow_heif import register_heif_opener

register_heif_opener()
class LecturePDF:
    EXIF_DATETIME_ORIGINAL = 36867
    EXIF_DATETIME = 306
    EXIF_DATETIME_DIGITIZED = 36868

    SUPPORTED_FORMATS = (".png", ".jpg", ".jpeg", ".heic", ".heif")

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.schedule = {}

    def set_schedule(self, schedule_path):
        try:
            with open(schedule_path, "r", encoding="utf-8") as f:
                self.schedule = json.load(f)
            if self.verbose:
                print(f"Schedule successfully loaded from {schedule_path}.")
        except Exception as e:
            print(f"schedule.json could not be read: {e}")
            self.schedule = {}

    def _get_week(self, photo_datetime, semester_starts):
        day_no = photo_datetime - semester_starts
        if day_no.days < 0:
            raise ValueError(
                f"Photo date ({photo_datetime.date()}) is before semester start ({semester_starts.date()}).")
        week_no = day_no.days // 7 + 1
        return week_no

    def _parse_date_from_filename(self, filepath):
        name = os.path.splitext(os.path.basename(filepath))[0]
        m = re.search(r'(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2})\.(\d{2})', name)
        if m:
            return f"{m.group(3)}:{m.group(2)}:{m.group(1)} {m.group(4)}:{m.group(5)}:00"
        return None

    def extract_photos_w_exif(self, file_list):
        exif_results = {}
        no_exif_found = []

        for full_path in file_list:
            if not full_path.lower().endswith(self.SUPPORTED_FORMATS):
                continue
            try:
                photo = Image.open(full_path)
                exif_data = photo.getexif()
                date_val = None

                if exif_data:
                    sub_ifd = exif_data.get_ifd(0x8769)
                    if sub_ifd:
                        date_val = sub_ifd.get(self.EXIF_DATETIME_ORIGINAL) or \
                                   sub_ifd.get(self.EXIF_DATETIME_DIGITIZED)
                    if not date_val:
                        date_val = exif_data.get(self.EXIF_DATETIME)

                if isinstance(date_val, bytes):
                    date_val = date_val.decode("utf-8").strip("\x00")

                if not date_val:
                    date_val = self._parse_date_from_filename(full_path)

                if date_val:
                    exif_results[full_path] = date_val
                else:
                    no_exif_found.append(full_path)

            except Exception as e:
                if self.verbose:
                    print(f"Error reading {full_path}: {e}")
                continue

        if no_exif_found and self.verbose:
            print("No date info found for:", len(no_exif_found), "files")

        if not exif_results and no_exif_found:
            raise ValueError(
                "None of the selected photos contain date information. "
                "This can happen with screenshots or photos shared via messaging apps.")

        return exif_results

    def _string_to_datetime(self, time_str):
        try:
            dt = datetime.strptime(time_str, "%Y:%m:%d %H:%M:%S")
            return dt
        except Exception:
            return None

    def _which_lecture(self, photo_time):
        photo_day = photo_time.weekday()
        photo_hour = photo_time.time()
        for lecture_name, sessions in self.schedule.items():
            for session in sessions:
                if session["day"] == photo_day:
                    start_time = datetime.strptime(
                        session["start_time"], "%H:%M").time()
                    end_time = datetime.strptime(
                        session["end_time"], "%H:%M").time()

                    if start_time <= photo_hour <= end_time:
                        return lecture_name

        return None

    def organize_photos(self, exif_results, semester_starts):
        date_exif_results = {}
        for key, value in exif_results.items():
            dt = self._string_to_datetime(value)
            if dt:
                date_exif_results[key] = dt

        sorted_date_exif_results = dict(
            sorted(date_exif_results.items(), key=lambda item: item[1]))

        photos_by_week_and_lecture = {}

        for photo_path, photo_datetime in sorted_date_exif_results.items():
            lecture = self._which_lecture(photo_datetime)
            if not lecture:
                continue

            week = self._get_week(photo_datetime, semester_starts)

            if week not in photos_by_week_and_lecture:
                photos_by_week_and_lecture[week] = {}

            if lecture not in photos_by_week_and_lecture[week]:
                photos_by_week_and_lecture[week][lecture] = []

            photos_by_week_and_lecture[week][lecture].append(photo_path)

        return photos_by_week_and_lecture

    def create_pdfs(self, photos_by_week_and_lecture, output_folder, db=None, schedule_name="", naming_format="week{week:02d}_{course}"):
        os.makedirs(output_folder, exist_ok=True)
        created_files = []

        for week, courses in photos_by_week_and_lecture.items():
            for course, photo_paths in courses.items():
                pdf = FPDF()

                for photo_path in photo_paths:
                    try:
                        photo = Image.open(photo_path)
                        photo = ImageOps.exif_transpose(photo)

                        temp_path = photo_path + ".temp.jpg"
                        photo.save(temp_path)

                        width, height = photo.size

                        if height >= width:
                            pdf.add_page(orientation="P")
                            pdf.image(temp_path, x=0, y=0, w=210, h=297)
                        else:
                            pdf.add_page(orientation="L")
                            pdf.image(temp_path, x=0, y=0, w=297, h=210)

                        if os.path.exists(temp_path):
                            os.remove(temp_path)

                    except Exception as e:
                        print(f"Error processing image {photo_path}: {e}")
                        continue

                course_name = course.replace(" ", "_").lower()
                schedule = schedule_name.replace(" ", "_").lower()
                num_photos = len(photo_paths)
                try:
                    filename = naming_format.format(
                        week=week, course=course_name,
                        schedule=schedule,
                        num_photos=num_photos) + ".pdf"
                except (KeyError, ValueError, IndexError):
                    filename = f"week{week:02d}_{course_name}.pdf"
                pdf_output_path = os.path.join(output_folder, filename)

                try:
                    pdf.output(pdf_output_path)
                    created_files.append(filename)
                    if db:
                        db.insert_pdf(
                            filename=filename,
                            filepath=pdf_output_path,
                            schedule=schedule_name,
                            week=week,
                            course=course
                        )
                except Exception as e:
                    print(f"Error saving PDF {filename}: {e}")

        return created_files
