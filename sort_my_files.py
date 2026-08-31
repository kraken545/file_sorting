"""sort_my_files.py - Copy files into category folders with a date prefix.

Scans a source directory (including subfolders), copies each file into one
of five category folders (images, documents, videos, apps, other) inside a
target directory, and renames the copy with an mtime-based date prefix.
Originals are never moved or deleted.

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
    ".png": "images",
    ".pdf": "documents",
    ".docx": "documents",
    ".mp4": "videos",
    ".avi": "videos",
    ".mkv": "videos",
    ".exe": "apps",
}


def collect_files(source_directory):
    files = []
    for root, _, names in os.walk(source_directory):
        for name in names:
            files.append(os.path.join(root, name))
    return files


def categorize_file(filename):
    extension = os.path.splitext(filename)[1].lower()
    return CATEGORIES.get(extension, "other")


def create_folders(directory):
    for category in sorted(set(CATEGORIES.values()) | {"other"}):
        os.makedirs(os.path.join(directory, category), exist_ok=True)


def start_key_listener(collapsed):
    if not sys.stdin.isatty():
        return None
    try:
        import select
        import termios
        import tty
    except ImportError:
        return None

    stop = threading.Event()

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
                        if collapsed[0]:
                            print()
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


def sort_files(source_directory, target_directory):
    start = time.perf_counter()
    files = collect_files(source_directory)
    print(f"Found {len(files)} file(s)")

    copied = 0
    errors = 0
    total_bytes = 0
    category_counts = {}
    category_bytes = {}

    collapsed = [False]
    listener = start_key_listener(collapsed)
    if listener is not None:
        collapsed[0] = True
        print("Progress: collapsed - press 'e' to expand, 'c' to collapse")

    for i, filepath in enumerate(files, 1):
        filename = os.path.basename(filepath)
        file_category = categorize_file(filename)
        target_path = os.path.join(target_directory, file_category, filename)
        if collapsed[0]:
            print(f"\rProgress: {i}/{len(files)} files ...", end="", flush=True)
        else:
            print(f"Copying: {filename} -> {file_category}/ ...")
        try:
            shutil.copy2(filepath, target_path)

            file_date = datetime.fromtimestamp(os.path.getmtime(filepath))

            # Replace colons to avoid invalid filename errors
            sanitized_date = file_date.isoformat().replace(":", "-")
            new_filename = f"{sanitized_date}-{filename}"

            os.rename(target_path, os.path.join(os.path.dirname(target_path), new_filename))

            copied += 1
            size = os.path.getsize(filepath)
            total_bytes += size
            category_counts[file_category] = category_counts.get(file_category, 0) + 1
            category_bytes[file_category] = category_bytes.get(file_category, 0) + size
        except Exception as e:
            errors += 1
            if collapsed[0]:
                print()
            print(f"  Error moving '{filepath}': {e}")

    if listener is not None:
        stop = listener[1]
        stop.set()
        listener[0].join(timeout=1)
    if collapsed[0]:
        print()
    elapsed = time.perf_counter() - start
    print(f"\nDone: {copied} file(s), {total_bytes / 1e6:.1f} MB")
    for category in sorted(category_counts):
        print(f"  {category}: {category_counts[category]} file(s), {category_bytes[category] / 1e6:.1f} MB")
    if errors:
        print(f"  Errors: {errors}")
    print(f"Time: {elapsed:.1f} s")


def main():
    source_directory = input("Source directory (Enter = current folder): ").strip() or "."
    target_directory = input("Destination directory (Enter = current folder): ").strip() or "."

    print(f"Sorting {source_directory} -> {target_directory} ...")
    create_folders(target_directory)
    sort_files(source_directory, target_directory)

    print("File organization completed!")


if __name__ == "__main__":
    main()