"""
Convert epubs in "New System" to cleaned .txt files, sorted into series folders.

DISCLAIMER - PERSONAL USE ONLY
  Use this only on DRM-free files you legally own or otherwise have the right
  to convert. This tool does NOT remove DRM and must not be used with any
  DRM-removal software; DRM-protected files will simply fail to convert.
  Converted files are for private reading only - do not share, sell, or
  redistribute them. Removing invisible characters fixes display issues; it
  does not change your license terms and must not be used to hide the source
  of a file for distribution. You are responsible for following copyright law
  and the terms of service of wherever you got your files.
  Provided "as is" with no warranty. The authors are not liable for data loss,
  misuse, or legal consequences. This is not legal advice. See README.md.

Expected layout (folder names are configurable below):

    <this script's folder>/
    ├─ epub_to_txt.py
    ├─ New System/                  <- source epubs (unstripped)
    │  ├─ Series A/
    │  │  ├─ Chapter 001.epub
    │  │  └─ Chapter 002.epub
    │  └─ Standalone Book.epub      <- loose epub: its own name becomes the series name
    └─ Clean Ver/                   <- must already exist
       ├─ Series A/                 <- your finished, cleaned library
       │  └─ Chapter 001.txt
       └─ _Holding/                 <- NEW .txt from each run lands here for review
          ├─ Series A/
          │  └─ Chapter 002.txt
          └─ Standalone Book/
             └─ Standalone Book.txt

How it works:
- Only epubs inside SOURCE_FOLDERS are processed; every other epub is ignored.
- Series name = the first folder under "New System" that the epub sits in
  (deeper subfolders are fine; they still count toward that series).
- Before converting, it scans ALL of "Clean Ver" (finished folders AND holding)
  and skips any epub whose series + filename already has a .txt.
- New .txt files are converted with Calibre, stripped of invisible Unicode
  characters, and saved to Clean Ver/_Holding/<Series>/. Move them into the
  main series folder yourself once you've checked them.
- Requires Calibre (ebook-convert). DRM-protected epubs are reported and skipped.
"""

import re
import shutil
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
SOURCE_FOLDERS = ["New System"]   # add more folder names here to include them
CLEAN_FOLDER = "Clean Ver"        # must already exist next to this script
HOLDING_FOLDER = "_Holding"       # created inside CLEAN_FOLDER if missing
CLEAN_INVISIBLE = True            # strip invisible characters after converting

# U+200B-U+200D: zero-width space / non-joiner / joiner
# U+2060-U+2064: word joiner, invisible function application/times/separator/plus
# U+FEFF:        zero-width no-break space (BOM)
INVISIBLE_CHARS = re.compile(r"[\u200B-\u200D\u2060-\u2064\uFEFF]")

# Default Calibre install locations, used if ebook-convert isn't on PATH
FALLBACK_PATHS = [
    Path(r"C:\Program Files\Calibre2\ebook-convert.exe"),
    Path(r"C:\Program Files (x86)\Calibre2\ebook-convert.exe"),
    Path("/Applications/calibre.app/Contents/MacOS/ebook-convert"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def find_ebook_convert() -> str | None:
    """Locate Calibre's ebook-convert executable."""
    on_path = shutil.which("ebook-convert")
    if on_path:
        return on_path
    for candidate in FALLBACK_PATHS:
        if candidate.exists():
            return str(candidate)
    return None


def series_name(epub: Path, source_root: Path) -> str:
    """
    The series is the first folder under the source root.
      New System/Series A/Chapter 1.epub          -> "Series A"
      New System/Series A/Vol 2/Chapter 9.epub    -> "Series A"
      New System/Standalone Book.epub             -> "Standalone Book"
    """
    parts = epub.relative_to(source_root).parts
    return parts[0] if len(parts) > 1 else epub.stem


def existing_txt_keys(clean_root: Path) -> set[tuple[str, str]]:
    """
    Collect (series, filename) for every .txt already anywhere in Clean Ver,
    including the holding folder. The series is the .txt's parent folder name.
    Lower-cased so "Chapter 1" and "chapter 1" count as the same file
    (Windows treats them as the same anyway).
    """
    return {
        (txt.parent.name.lower(), txt.stem.lower())
        for txt in clean_root.rglob("*.txt")
    }


def convert(converter: str, epub: Path, txt: Path) -> tuple[bool, str]:
    """Run ebook-convert. Returns (success, error message if any)."""
    result = subprocess.run(
        [converter, str(epub), str(txt), "--txt-output-encoding", "utf-8"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode == 0 and txt.exists():
        return True, ""
    # The last non-empty line of Calibre's output is usually the real error
    lines = [ln for ln in (result.stderr or result.stdout).splitlines() if ln.strip()]
    return False, lines[-1] if lines else f"exit code {result.returncode}"


def strip_invisible(txt: Path) -> int:
    """Remove invisible characters in place. Returns how many were removed."""
    text = txt.read_text(encoding="utf-8")
    cleaned, removed = INVISIBLE_CHARS.subn("", text)
    if removed:
        txt.write_text(cleaned, encoding="utf-8")
    return removed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    base = Path(__file__).resolve().parent
    clean_root = base / CLEAN_FOLDER
    holding_root = clean_root / HOLDING_FOLDER

    if not clean_root.is_dir():
        print(f'Couldn\'t find the "{CLEAN_FOLDER}" folder next to this script. '
              "Create it (or change CLEAN_FOLDER at the top of the script) and run again.")
        return

    converter = find_ebook_convert()
    if not converter:
        print("Couldn't find Calibre's ebook-convert. Install Calibre, or add its "
              "folder to PATH, or add its location to FALLBACK_PATHS in this script.")
        return

    # Gather (epub, series) pairs from the source folders only
    jobs: list[tuple[Path, str]] = []
    for folder_name in SOURCE_FOLDERS:
        source_root = base / folder_name
        if not source_root.is_dir():
            print(f'NOTE: source folder "{folder_name}" not found, skipping it.')
            continue
        for epub in sorted(source_root.rglob("*.epub")):
            jobs.append((epub, series_name(epub, source_root)))

    if not jobs:
        print(f"No .epub files found in: {', '.join(SOURCE_FOLDERS)}")
        return

    already_done = existing_txt_keys(clean_root)
    converted = skipped = failed = 0

    for epub, series in jobs:
        label = f"{series} / {epub.name}"

        if (series.lower(), epub.stem.lower()) in already_done:
            print(f"SKIPPED    {label} (.txt already in {CLEAN_FOLDER})")
            skipped += 1
            continue

        out_dir = holding_root / series
        out_dir.mkdir(parents=True, exist_ok=True)
        txt = out_dir / f"{epub.stem}.txt"

        print(f"Converting {label} ...", end=" ", flush=True)
        ok, error = convert(converter, epub, txt)
        if not ok:
            print(f"FAILED: {error}")
            failed += 1
            continue

        note = ""
        if CLEAN_INVISIBLE:
            removed = strip_invisible(txt)
            note = f" (removed {removed:,} invisible chars)" if removed else ""
        print(f"done{note}")
        already_done.add((series.lower(), epub.stem.lower()))
        converted += 1

    print(f"\nFinished: {converted} converted, {skipped} skipped, {failed} failed.")
    if converted:
        print(f"New files are in: {holding_root}")


if __name__ == "__main__":
    main()
