# File Sorting

A single-file Python CLI tool that **sorts your files into category folders**:
it scans a source directory (including all subfolders), copies every file into
one of five folders — `images`, `documents`, `videos`, `apps`, `other` — inside
a destination directory, and renames each copy with an **mtime-based date
prefix** (when the file was last modified).

Your originals are **never moved or deleted** — the tool only copies. Run it,
watch it work, and get a short summary at the end.

## Requirements

- **Python 3** (standard library only, no dependencies to install)

## Quick start

```bash
python sort_my_files.py
```

## How to use it

The tool asks for two directories, then does everything automatically:

```
Source directory (Enter = current folder): /home/user/Downloads
Destination directory (Enter = current folder): /home/user/Organized
```

- **Source**: where your messy files are (subfolders are scanned too)
- **Destination**: where the category folders will be created / filled

Press **Enter** with an empty answer to use the current folder.

You can **drag & drop a folder onto the terminal** to paste its path.

## Progress display

While sorting, the tool shows progress on a **single line** so the terminal
doesn't fill up:

```
Progress: 137/500 files ...
```

During the run you can toggle the display at any time:

- press **e** to **expand** — one line per file (`Copying: photo.jpg -> images/ ...`)
- press **c** to **collapse** — back to the single progress line

(Collapse/expand keys work on Linux and WSL; when output is piped, the tool
always shows the full per-file lines.)

## What it does

1. Creates the five category folders in the destination (even if a category ends up empty).
2. Scans the source and reports how many files it found.
3. Copies each file into its category folder, showing progress as it goes.
4. Renames the copy to `date-prefixed-filename` (e.g. `2026-08-31T12-47-05.123456-photo.jpg`) so files are naturally ordered by modification time. The date includes microseconds, so same-named files from different subfolders still get unique names.

### Categories

| Extension | Folder |
|-----------|--------|
| `.jpg`, `.png` | `images` |
| `.pdf`, `.docx` | `documents` |
| `.mp4`, `.avi`, `.mkv` | `videos` |
| `.exe` | `apps` |
| anything else | `other` |

## Example run (expanded view)

```
Found 4 file(s)
Progress: collapsed - press 'e' to expand, 'c' to collapse
Copying: photo.jpg -> images/ ...
Copying: song.mp4 -> videos/ ...
Copying: report.pdf -> documents/ ...
Copying: notes.txt -> other/ ...
  Error moving '/home/user/Downloads/broken.pdf': [Errno 2] No such file

Done: 3 file(s), 12.5 MB
  documents: 1 file(s), 0.2 MB
  images: 1 file(s), 3.1 MB
  videos: 1 file(s), 9.2 MB
Time: 0.3 s
File organization completed!
```

## Notes

- Failed files don't stop the run: each error is printed (indented, two spaces) and the tool continues with the next file.
- Running the tool again on the same destination **re-copies and re-prefixes** the already-organized files (the destination folder is not excluded from the scan). Point it at a fresh destination, or delete the organized folders first.
- Files with the same name from different source subfolders end up in the same category folder; since the date prefix includes microseconds, they are kept separate only if their modification times differ.