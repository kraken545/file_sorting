"""sort_my_files.py - Copy files into category folders with a date prefix.

Scans a source directory (including subfolders), copies each file into one
of five category folders (images, documents, videos, apps, other) inside a
target directory, and renames the copy with an mtime-based date prefix.
After all successful copies have been checked, their original files are deleted.

Progress shows a single line by default; press 'e' to expand it into
per-file lines, 'c' to collapse it again.

Usage: python sort_my_files.py
"""

import os
import shutil
import sys
import threading
import time
from datetime import datetime

CATEGORIES = {
    ".jpg": "images",
    ".jpeg": "images",
    ".png": "images",
    ".gif": "images",
    ".webp": "images",
    ".pdf": "documents",
    ".doc": "documents",
    ".docx": "documents",
    ".xls": "documents",
    ".xlsx": "documents",
    ".ppt": "documents",
    ".pptx": "documents",
    ".txt": "documents",
    ".mp4": "videos",
    ".avi": "videos",
    ".mkv": "videos",
    ".mov": "videos",
    ".wmv": "videos",
    ".webm": "videos",
    ".exe": "apps",
    ".msi": "apps",
}


def collect_files(source_directory, excluded_directories):
    files = []
    for root, directories, names in os.walk(source_directory):
        directories[:] = [
            directory
            for directory in directories
            if os.path.realpath(os.path.join(root, directory)) not in excluded_directories
        ]
        for name in names:
            files.append(os.path.join(root, name))
    return files


def categorize_file(filename):
    extension = os.path.splitext(filename)[1].lower()
    return CATEGORIES.get(extension, "other")


def create_folders(directory):
    for category in sorted(set(CATEGORIES.values()) | {"other"}):
        os.makedirs(os.path.join(directory, category), exist_ok=True)


def get_excluded_directories(source_directory, target_directory):
    source_path = os.path.realpath(source_directory)
    target_path = os.path.realpath(target_directory)
    category_directories = {
        os.path.join(target_path, category)
        for category in set(CATEGORIES.values()) | {"other"}
    }

    if target_path == source_path:
        return category_directories
    try:
        target_is_inside_source = os.path.commonpath([source_path, target_path]) == source_path
    except ValueError:
        target_is_inside_source = False
    if target_is_inside_source:
        return {target_path}
    return set()


def get_available_target_path(directory, filename, modified_time):
    date_prefix = datetime.fromtimestamp(modified_time).isoformat().replace(":", "-")
    name, extension = os.path.splitext(filename)
    candidate = os.path.join(directory, f"{date_prefix}-{filename}")
    number = 1

    while os.path.exists(candidate):
        candidate = os.path.join(directory, f"{date_prefix}-{name}-{number}{extension}")
        number += 1

    return candidate


def remove_verified_original(filepath, target_path, source_size, source_mtime_ns):
    source_info = os.stat(filepath)
    if source_info.st_size != source_size or source_info.st_mtime_ns != source_mtime_ns:
        raise OSError("Source file changed after copy")

    target_info = os.stat(target_path)
    if target_info.st_size != source_size:
        raise OSError("Copied file size does not match source")

    os.remove(filepath)


def format_progress(index, total, completed, errors, prefix="Progress", completed_label="copied"):
    percent = int(index / total * 100) if total else 0
    error_label = "error" if errors == 1 else "errors"
    terminal_width = shutil.get_terminal_size(fallback=(80, 24)).columns
    available_width = max(1, terminal_width - 1)
    wide_details = f" {index}/{total} ({percent}%) | {completed} {completed_label} | {errors} {error_label}"
    short_details = f" {index}/{total} ({percent}%)"

    if available_width >= len(f"{prefix}: []") + len(wide_details) + 10:
        details = wide_details
        minimum_bar_width = 10
    elif available_width >= len(f"{prefix}: []") + len(short_details) + 5:
        details = short_details
        minimum_bar_width = 5
    else:
        details = f" {percent}%"
        minimum_bar_width = 1

    bar_width = max(
        minimum_bar_width,
        min(30, available_width - len(f"{prefix}: []") - len(details)),
    )
    filled = int(bar_width * percent / 100)
    bar = "#" * filled + "-" * (bar_width - filled)
    return f"{prefix}: [{bar}]{details}"


def print_progress(
    index,
    total,
    completed,
    errors,
    previous_length,
    prefix="Progress",
    completed_label="copied",
):
    line = format_progress(index, total, completed, errors, prefix, completed_label)
    terminal_width = shutil.get_terminal_size(fallback=(80, 24)).columns
    padding = ""

    if len(line) < previous_length[0]:
        if previous_length[0] < terminal_width:
            padding = " " * (previous_length[0] - len(line))
        else:
            print()

    print(f"\r{line}{padding}", end="", flush=True)
    previous_length[0] = len(line)


def start_key_listener(collapsed):
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return None

    stop = threading.Event()

    if os.name == "nt":
        import msvcrt

        def listen():
            while not stop.is_set():
                if msvcrt.kbhit():
                    char = msvcrt.getwch().lower()
                    if char == "c":
                        collapsed[0] = True
                    elif char == "e":
                        collapsed[0] = False
                time.sleep(0.1)

        thread = threading.Thread(target=listen, daemon=True)
        thread.start()
        return thread, stop

    try:
        import select
        import termios
        import tty
    except ImportError:
        return None

    def listen():
        fd = sys.stdin.fileno()
        old_settings = None
        try:
            old_settings = termios.tcgetattr(fd)
            tty.setcbreak(fd)
        except Exception:
            return
        try:
            while not stop.is_set():
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    char = sys.stdin.read(1)
                    if char == "c":
                        collapsed[0] = True
                    elif char == "e":
                        collapsed[0] = False
        finally:
            if old_settings is not None:
                try:
                    termios.tcsetattr(fd, termios.TCSADRAIN, fd, old_settings)
                except Exception:
                    pass

    thread = threading.Thread(target=listen, daemon=True)
    thread.start()
    return thread, stop


def sort_files(source_directory, target_directory, excluded_directories):
    start = time.perf_counter()
    files = collect_files(source_directory, excluded_directories)
    print(f"Found {len(files)} file(s)")

    copied = 0
    removed = 0
    errors = 0
    total_bytes = 0
    category_counts = {}
    category_bytes = {}

    collapsed = [False]
    previous_progress_length = [0]
    last_view_was_collapsed = False
    listener = start_key_listener(collapsed)
    if listener is not None:
        collapsed[0] = True
        print("View: compact | e: details, c: compact")
        print_progress(0, len(files), copied, errors, previous_progress_length)
        last_view_was_collapsed = True

    for i, filepath in enumerate(files, 1):
        filename = os.path.basename(filepath)
        file_category = categorize_file(filename)
        if not collapsed[0]:
            if last_view_was_collapsed:
                print()
            print(f"Copying: {filename} -> {file_category}/ ...")
        try:
            file_info = os.stat(filepath)
            category_directory = os.path.join(target_directory, file_category)
            target_path = get_available_target_path(
                category_directory, filename, file_info.st_mtime
            )
            shutil.copy2(filepath, target_path)
            target_info = os.stat(target_path)
            if target_info.st_size != file_info.st_size:
                raise OSError("Copied file size does not match source")

        except Exception as e:
            errors += 1
            if collapsed[0]:
                print()
                previous_progress_length[0] = 0
            print(f"  Error moving '{filepath}': {e}")
        else:
            copied += 1
            size = file_info.st_size
            total_bytes += size
            category_counts[file_category] = category_counts.get(file_category, 0) + 1
            category_bytes[file_category] = category_bytes.get(file_category, 0) + size
            try:
                os.remove(filepath)
            except Exception as e:
                errors += 1
                if collapsed[0]:
                    print()
                    previous_progress_length[0] = 0
                print(f"  Error moving '{filepath}': {e}")
            else:
                removed += 1
        if collapsed[0]:
            if not last_view_was_collapsed:
                previous_progress_length[0] = 0
            print_progress(i, len(files), copied, errors, previous_progress_length)
        elif last_view_was_collapsed:
            print()
        last_view_was_collapsed = collapsed[0]

    if listener is not None:
        stop = listener[1]
        stop.set()
        listener[0].join(timeout=1)
    if collapsed[0]:
        print()
    elapsed = time.perf_counter() - start
    print(f"\nDone: {copied} file(s), {total_bytes / 1e6:.1f} MB")
    print(f"Removed: {removed} original file(s)")
    for category in sorted(category_counts):
        print(f"  {category}: {category_counts[category]} file(s), {category_bytes[category] / 1e6:.1f} MB")
    if errors:
        print(f"  Errors: {errors}")
    if copied > removed:
        print(f"  Originals kept: {copied - removed} file(s) after deletion errors")
    print(f"Time: {elapsed:.1f} s")


def main():
    source_directory = input("Source directory (Enter = current folder): ").strip() or "."
    target_directory = input("Destination directory (Enter = current folder): ").strip() or "."

    if not os.path.isdir(source_directory):
        print(f"Source directory does not exist or is not a folder: {source_directory}")
        return
    if os.path.exists(target_directory) and not os.path.isdir(target_directory):
        print(f"Destination path is not a folder: {target_directory}")
        return

    print(f"Sorting {source_directory} -> {target_directory} ...")
    try:
        create_folders(target_directory)
    except OSError as error:
        print(f"Could not create destination folders: {error}")
        return

    print("Original files are deleted after a verified copy")
    excluded_directories = get_excluded_directories(source_directory, target_directory)
    if excluded_directories:
        print("Destination folders are excluded from the scan")
    sort_files(source_directory, target_directory, excluded_directories)

    print("File organization completed!")


if __name__ == "__main__":
    main()
