import argparse
import os
import sys
from datetime import datetime

from src.core.pdf_engine import LecturePDF
from src.utils.platform import PLATFORM


def main():
    if len(sys.argv) == 1 and PLATFORM == "win32" and getattr(sys, "frozen", False):
        import msvcrt
        print("This program must be run from a command line. Do not double-click the executable.")
        print("Usage: lecturepdf --semester-start YYYY-MM-DD [OPTIONS]")
        print("\nFor more information, see: lecturepdf --help")
        msvcrt.getch()
        sys.exit(2)

    parser = argparse.ArgumentParser(description="LecturePDF CLI")

    parser.add_argument(
        "-pf", "--photos-folder", default="./input", help="Path of folder containing photos. A folder path can be specified otherwise it will take the folder named input where the executable is in.")
    parser.add_argument("-sf", "--schedule-file", default="schedule.json",
                        help="Path of Schedule JSON file. A .json path can be specified otherwise it will check the folder where the executable is in. See the sample.json for the format.")
    parser.add_argument("-of", "--output-folder", default="output",
                        help="Path of output folder for PDFs. A folder path can be specified otherwise it will check the folder where the executable is in.")
    parser.add_argument("-ss", "--semester-start", type=str,
                        help="Semester start date in YYYY-MM-DD format", required=True)
    parser.add_argument("-q", "--quiet", action="store_false", dest="verbose", default=True, help="Toggle quite mode. No log messages.")


    args = parser.parse_args()
    
    try:
        semester_start = datetime.strptime(args.semester_start, "%Y-%m-%d")
    except ValueError:
        print("ERROR: Invalid semester_start format. Use YYYY-MM-DD.")
        sys.exit(1)

    folder_path = args.photos_folder
    if not os.path.isdir(folder_path):
        print(f"ERROR: Photos folder not found: {folder_path}")
        sys.exit(1)

    file_list = []
    for f in os.listdir(folder_path):
        full_path = os.path.join(folder_path, f)
        if os.path.isfile(full_path):
            file_list.append(full_path)

    if not file_list:
        print(f"ERROR: No files found in {folder_path}")
        sys.exit(1)

    try:
        app = LecturePDF(verbose=args.verbose)
        app.set_schedule(args.schedule_file)
        exif_data = app.extract_photos_w_exif(file_list)
        organized = app.organize_photos(exif_data, semester_start)
        created = app.create_pdfs(organized, args.output_folder)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if args.verbose:
        print(f"✓ PDF creation completed. {len(created)} PDFs created.")


if __name__ == "__main__":
    main()
