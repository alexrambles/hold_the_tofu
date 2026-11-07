# hold_the_tofu

Two scripts for tidying up DRM-free epubs:

| Script | What it does |
|---|---|
| [`epub_to_txt.py`](#epub_to_txtpy) | Converts the epubs in **New System** into cleaned `.txt` files, one folder per series, and puts them in a holding area inside **Clean Ver** so you can look them over before filing them. |
| [`epub_cleaner.py`](#epub_cleanerpy) | Cleans a single epub and saves it as a new epub (`<name>_clean.epub`). |

"Cleaned" means the invisible Unicode characters are removed (zero-width spaces, word joiners, invisible separators, BOMs). These are the characters that show up as boxes in a text editor. Some stores add them to the text as a watermark.

> ### ⚠️ Disclaimer: personal use only
>
> **Read this before using either script.**
>
> - **Only use this on DRM-free files you legally own**, or that you otherwise have the right to copy and convert, such as your own writing, public-domain works, or files whose license allows format conversion.
> - **This tool does not remove DRM and must not be used to try to.** It doesn't include, call, or support any DRM-removal method. DRM-protected files will simply fail to convert. Don't combine this tool with DRM-removal software.
> - **The converted files are for your own private reading only.** Don't share, upload, sell, or redistribute them, whether cleaned or not.
> - **Removing invisible characters is meant to fix how the text displays.** It is not meant to hide where a file came from. If a publisher or store uses these characters as a watermark, removing them doesn't change your license terms or what you're allowed to do with the file. Using this tool to hide the source of a file you plan to distribute is strictly prohibited.
> - **Follow your local copyright laws and the terms of service** of wherever you got the files. Some stores' terms restrict converting or modifying purchased files. You are responsible for checking yours.
> - **No warranty.** This software is provided "as is," with no guarantee of any kind. The authors aren't responsible for data loss, damage, or any misuse, and aren't responsible for any legal consequences of how you use it. Keep backups of anything you care about.
> - **This is not legal advice.** If you aren't sure whether you're allowed to convert a particular file, don't convert it.
>
> By using these scripts, you agree that you are solely responsible for making sure your use is lawful.

---

## Requirements

- **Python 3.10 or newer**
- **Python packages** (for `epub_cleaner.py` only). Install them from the script's folder with:

  ```
  pip install -r requirements.txt
  ```

  This installs `EbookLib`, `beautifulsoup4` and `lxml`.
- **Calibre** (for `epub_to_txt.py` only), installed normally. The script uses Calibre's command-line converter, `ebook-convert`, which comes with it. The script looks for it on your PATH first, then in the default install locations:
  - `C:\Program Files\Calibre2\`
  - `C:\Program Files (x86)\Calibre2\`
  - `/Applications/calibre.app/` (macOS)

`epub_to_txt.py` doesn't need any pip packages. It only uses Python's standard library.

---

# epub_to_txt.py

## Folder structure

```
<any folder>/
├─ epub_to_txt.py
├─ README.md
│
├─ New System/                     ← SOURCE: put your epubs here
│  ├─ Series A/                    ← one folder per series
│  │  ├─ Chapter 001.epub
│  │  ├─ Chapter 002.epub
│  │  └─ Vol 2/                    ← deeper subfolders are OK
│  │     └─ Chapter 009.epub       ←   (still counts as "Series A")
│  ├─ Series B/
│  │  └─ Book.epub
│  └─ Standalone Book.epub         ← loose epub: its own name becomes the series name
│
└─ Clean Ver/                      ← OUTPUT: must already exist
   ├─ Series A/                    ← your finished library (you manage this)
   │  └─ Chapter 001.txt
   └─ _Holding/                    ← created automatically; new files land here
      ├─ Series A/
      │  ├─ Chapter 002.txt
      │  └─ Chapter 009.txt
      ├─ Series B/
      │  └─ Book.txt
      └─ Standalone Book/
         └─ Standalone Book.txt
```

### Rules

| Rule | Details |
|---|---|
| **The script sits next to `New System` and `Clean Ver`** | Folder paths are worked out from where the `.py` file is, not from where you run it. |
| **`Clean Ver` must already exist** | If it's missing, the script stops with a message. It won't create it for you. |
| **Only `New System` is read** | Epubs anywhere else (loose next to the script, other folders) are ignored. |
| **Series name = first folder under `New System`** | `New System/Series A/Vol 2/Ch 9.epub` → series **Series A**. |
| **Loose epubs become their own series** | `New System/Standalone Book.epub` → `_Holding/Standalone Book/Standalone Book.txt`. |
| **Nested folders are flattened** | Everything under `Series A/` goes into a single `Series A/` output folder. If two volumes both have `Chapter 1.epub`, the second one is skipped as a duplicate (see below). |

---

## How to run

From a terminal in the script's folder:

```
python epub_to_txt.py
```

Double-clicking the file also works on Windows, but the window closes as soon as the script finishes, so you won't see the summary.

### What happens on each run

1. **Clean Ver is scanned** for every `.txt` already there, in your finished series folders and in `_Holding`, at any depth.
2. **Each epub in New System is checked** against that list. If a `.txt` with the same **series + filename** exists, the epub is **skipped**. Nothing gets converted, stripped, or overwritten.
3. **New epubs are converted** with Calibre and saved to `Clean Ver/_Holding/<Series>/`.
4. **Invisible characters are removed** from each new `.txt`.
5. **A summary is printed:** how many were converted, skipped, and failed.

### Your part afterward

Look over the files in `_Holding`, then move them into `Clean Ver/<Series>/`. Files stay "already done" whether they're in `_Holding` or in the main folder, so you can move them whenever you like without causing re-conversions.

---

## Settings

All settings are at the top of `epub_to_txt.py`.

| Variable | Default | What it does |
|---|---|---|
| `SOURCE_FOLDERS` | `["New System"]` | The folder(s) to read epubs from, relative to the script. Add more names to include other folders, e.g. `["New System", "Imports"]`. A missing folder is noted and skipped. |
| `CLEAN_FOLDER` | `"Clean Ver"` | The output folder, which must already exist. It's also where the script checks for existing `.txt` files. |
| `HOLDING_FOLDER` | `"_Holding"` | The subfolder inside `CLEAN_FOLDER` where new `.txt` files go. It's created automatically. The leading `_` keeps it at the top of the folder list. |
| `CLEAN_INVISIBLE` | `True` | Removes invisible characters after converting. Set to `False` to keep Calibre's raw output. |
| `INVISIBLE_CHARS` | see script | The list of characters that get removed: `U+200B–U+200D`, `U+2060–U+2064`, `U+FEFF`. You'd only change this if you find a different invisible character in your files. |
| `FALLBACK_PATHS` | Calibre default installs | Where to look for `ebook-convert` if it isn't on your PATH. Add your own path here if Calibre is installed somewhere unusual. |

---

## How "already converted" is decided

An epub is skipped when `Clean Ver` (including `_Holding`) contains a `.txt` where both of these are true:

- **the filename matches** the epub's filename, apart from the extension, and
- **the folder it's in** has the same name as the epub's series.

The comparison ignores upper and lower case, so `Chapter 1` and `chapter 1` count as the same.

**Where this can go wrong:** if a finished `.txt` was renamed, or its series folder is spelled differently from the one in New System, the script won't recognize it. You'll get a new copy in `_Holding`. Your existing file is never touched, because the script only writes inside `_Holding`.

**To re-convert a file:** delete (or move out of Clean Ver) its `.txt`, then run the script again.

---

## Output messages

| Message | Meaning |
|---|---|
| `SKIPPED  Series / file.epub (.txt already in Clean Ver)` | A matching `.txt` already exists, so nothing was done. |
| `Converting Series / file.epub ... done (removed N invisible chars)` | The file was converted and cleaned. |
| `Converting ... done` | The file was converted and had no invisible characters. |
| `Converting ... FAILED: <reason>` | Calibre couldn't convert it. The most common cause is DRM (copy protection). A corrupt file is another. The script moves on to the next file. |
| `NOTE: source folder "X" not found` | A folder listed in `SOURCE_FOLDERS` doesn't exist. |
| `Couldn't find the "Clean Ver" folder` | Create the folder, or fix `CLEAN_FOLDER`. |
| `Couldn't find Calibre's ebook-convert` | Install Calibre, or add its path to `FALLBACK_PATHS`. |

---

## Safety

- **Epubs are never changed**, moved, or deleted.
- **Nothing outside `Clean Ver/_Holding/` is written.** Your finished series folders are only read, never written to.
- **Existing `.txt` files are never overwritten**, because anything that matches is skipped before conversion.

---

# epub_cleaner.py

Cleans one epub and saves the result as a new epub. The original file isn't changed.

## What it removes

From every chapter:

- HTML comments
- Invisible characters (zero-width spaces, joiners, word joiners, invisible separators)
- Non-breaking spaces, which are replaced with normal spaces
- Stray carriage-return entities (`&#13;`, `&#xd;`)

From the book's metadata:

- Tracking fields: `opennovel:user_id`, `book-token` and `dtb:uid`

It also gives the book a new random identifier and sets its title to the filename, without the folder path or the `.epub` extension.

## How to run

1. Install the Python packages (see [Requirements](#requirements)).
2. Open a terminal in the folder that holds your epub.
3. Run:

   ```
   python epub_cleaner.py
   ```

4. At `Enter book file name:`, type the epub's filename (for example `My Book.epub`) or paste its full path (for example `"C:\Books\My Book.epub"`). Quotes around it are fine.
5. The cleaned copy is saved next to the original as `My Book_clean.epub`.

If you type just a filename, it's looked for in the folder your terminal is in, not the script's folder. This is different from `epub_to_txt.py`.

## Settings

| Variable | Default | What it does |
|---|---|---|
| `STRIP_ID_CLASS` | `False` | Set to `True` to also remove every `id` and `class` attribute. This can change how the book looks in some readers. |
| `META_NAMES_TO_REMOVE` | see script | The metadata fields that get removed. |

## Things to know

- **An existing `_clean.epub` with the same name is overwritten** without asking.
- **Images, fonts and stylesheets are kept.** If a book has images that aren't listed in its manifest (its internal file list), they're added to the list so they aren't lost, and each one is reported as `Kept unlisted image: ...`.

---

# Using both together

You don't need to run `epub_cleaner.py` before `epub_to_txt.py`, because `epub_to_txt.py` already removes invisible characters.

To keep a cleaned epub as well as the `.txt`:

1. Run `epub_cleaner.py` on the book.
2. Move the `_clean.epub` into `New System/` (or a series folder inside it).
3. Run `epub_to_txt.py`.

The `.txt` will be named after the `_clean.epub`, for example `My Book_clean.txt`.
