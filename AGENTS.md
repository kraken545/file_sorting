# AGENTS.md

## Repo

- Single file: `sort_my_files.py` (stdlib only: `os`, `shutil`, `datetime`, `time`, plus `sys`, `threading`). Not a git repo. No tests, no deps.
- Run: `python sort_my_files.py` — interactive only (two `input()` prompts, no CLI args). Prompts are plain and professional (`Source directory (Enter = current folder): ...`); the old Star Wars "Lord Vinson"/"Lord Vader" text was removed at the user's request — don't bring it back.

## Behavior to preserve

- **Copies, never moves**: `shutil.copy2` keeps originals in place. Do not switch to `shutil.move` — that deletes user data.
- Sorts by extension (8-entry dict: jpg/png→images, pdf/docx→documents, mp4/avi/mkv→videos, exe→apps), unknown → `other`.
- `create_folders` always creates all 5 category folders up front (even empty ones).
- Copies get renamed with an mtime-based prefix: `datetime.isoformat().replace(":", "-")` + filename. The microsecond component is what disambiguates same-named files — don't drop it.
- `copy2` must stay: it preserves mtime, which the date prefix depends on.
- Per-file `try/except Exception` prints the error and continues; never abort the whole run.
- Progress UI: single `\r` line by default (`Progress: {i}/{n} files ...`, `flush=True`), expandable with per-file `Copying: {name} -> {category}/ ...` lines. Pressing **e** expands, **c** collapses — read by a daemon listener thread (`start_key_listener`, stdlib `termios`/`tty`/`select` in cbreak mode) that only starts when stdin is a tty. Piped output always runs expanded. Don't remove or replace this with tqdm/rich; restore the terminal settings via the thread's `finally` (already handled by `stop` + `join(timeout=1)`).

## Known gotchas (do not "fix" silently)

- `target_path` is never checked — same-named files from different source subfolders silently overwrite each other (copy and rename both). Uniquifying is a behavior change: propose it, don't ship it.
- `os.walk` does not exclude the target dir; if target is inside source (or on re-runs), already-organized files get re-copied and re-prefixed (runaway duplication). Skipping the target is a fix — confirm with user before applying.
- Print `Error moving '{filepath}': {e}` — keep the wording "moving" even though it copies.

## House style (match the user's other repos: kraken545/audio_tool, kraken545/img_tool)

- Plain `print()` only: no `colorama`, `tqdm`, `rich`, no emoji, no ANSI colors, no `[ERROR]` banners.
- `snake_case` functions, `ALL_CAPS` constants (e.g. `CATEGORIES`), module docstring at top, `main()` guarded by `if __name__ == "__main__":`.
- Per-file progress lines end with `...`: `print(f"Processing: {name} ...")`; errors are two-space indented and lowercase: `print(f"  Error ...")`.
- Summaries: blank line + `\nDone: {n} file(s)` with counts; MB via `/ 1e6`, `.1f` formatting; `(Enter = default)` prompts with `.strip() or "default"`.
- Build the file list first (collect pattern), print `Found {n} file(s)` before processing.

## Active intent (current session focus)

The informative-output work is done: per-file/collapsed progress, end-of-run summary (per-category counts + MB, total, elapsed time via `time.perf_counter()`), and the collapsible/expandable progress UI (`e`/`c` keys). If the user asks for more, keep it stdlib-`print()`-only, no new dependencies without explicit approval.