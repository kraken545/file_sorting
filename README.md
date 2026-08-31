# File Sorting

A small Python command-line tool that organizes files safely: it copies each
file to its category, verifies the copy's size, then deletes the original.

```
Source folder  ->  copy and verify  ->  organized destination
Downloads      ->  images / documents ->  original removed only on success
                    videos / apps / other
```

## Highlights

- Copies files with `shutil.copy2`, verifies the destination size, then removes
  only the successfully copied original.
- Scans source subfolders and creates every category folder up front.
- Preserves modification times and prefixes each copy with that date.
- Keeps duplicate output names by adding `-1`, `-2`, and so on when necessary.
- Automatically excludes the destination folders when they are inside the source,
  preventing organized copies from being processed again.
- Shows progress, category totals, removed originals, total size, elapsed time,
  and non-fatal errors.
- Uses only the Python standard library.

## Requirements

- Python 3

No installation or additional packages are needed.

## Quick start

```bash
python sort_my_files.py
```

Enter the source and destination folders when prompted. Press Enter at either
prompt to use the current folder.

```
Source directory (Enter = current folder): C:\Users\you\Downloads
Destination directory (Enter = current folder): C:\Users\you\Organized
```

You can also drag a folder onto many terminals to paste its path.

## What happens

1. The five category folders are created in the destination, including empty ones.
2. Files in the source and its subfolders are collected.
3. Destination folders are skipped if they sit inside the source folder.
4. Each file is copied to its category with a modification-date prefix.
5. The destination size is checked against the source size.
6. Only after that check succeeds is the original file deleted.
7. A summary reports copied files, removed originals, sizes, errors, and elapsed time.

Example output filename:

```
2026-08-31T12-47-05.123456-photo.jpg
2026-08-31T12-47-05.123456-photo-1.jpg
```

The second form is used only when the first name already exists, so no output
file is silently overwritten.

## Categories

| Extensions | Destination folder |
|---|---|
| `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp` | `images` |
| `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`, `.txt` | `documents` |
| `.mp4`, `.avi`, `.mkv`, `.mov`, `.wmv`, `.webm` | `videos` |
| `.exe`, `.msi` | `apps` |
| Anything else | `other` |

## Progress display

In an interactive terminal, progress starts collapsed:

```
Progress: [########----------------------] 137/500 (27%) | 136 copied | 1 error
```

- Press `e` to expand to one line per file.
- Press `c` to return to the compact progress line.

The ASCII bar adapts to the terminal width. On narrow terminals it keeps the
file count and percentage while omitting the extra counters. The keyboard
controls work on Windows, Linux, and WSL. If input or output is piped, the
script prints the detailed lines instead.

## Example run

```
Sorting C:\Users\you\Downloads -> C:\Users\you\Organized ...
Original files are deleted after a verified copy
Found 4 file(s)
View: compact | e: details, c: compact
Progress: [##############################] 4/4 (100%) | 4 copied | 0 errors

Done: 4 file(s), 12.5 MB
Removed: 4 original file(s)
  documents: 1 file(s), 0.2 MB
  images: 1 file(s), 3.1 MB
  other: 1 file(s), 0.1 MB
  videos: 1 file(s), 9.1 MB
Time: 0.3 s
File organization completed!
```

## Safety notes

- An original is deleted only after `copy2` succeeds and the copy has the same
  size as the original.
- If copying, verification, or deletion fails, that file is reported as an error
  and the original is kept. The rest of the run continues.
- If the source folder does not exist, or the destination is a file instead of a
  folder, the program explains the problem before copying anything.
- If source and destination are the same folder, the generated category folders
  are excluded from scanning. Files elsewhere in that folder can still be copied
  into those categories.
