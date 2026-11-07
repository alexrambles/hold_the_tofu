import os
from ebooklib import epub, ITEM_DOCUMENT
import re
from bs4 import BeautifulSoup, Comment
import uuid
import zipfile
import mimetypes
import posixpath
from urllib.parse import unquote
from xml.etree import ElementTree


OPF_NS = "http://www.idpf.org/2007/opf"

META_NAMES_TO_REMOVE = {"opennovel:user_id", "book-token", "dtb:uid"}

COMMENT_REMOVE = re.compile("<!--.*?-->", re.DOTALL)

INVISIBLES_REMOVE = re.compile("[\u200B|\u200C|\u200D|\u2060|\u2061|\u2062|\u2063|\u2064]")

NBSP = re.compile("\u00a0|&nbsp;|&#160;|&#xa0;", re.IGNORECASE)

LINEBREAKS = re.compile(r"&#(?:0*13|x0*d);", re.IGNORECASE)


#optional also strip id/class
STRIP_ID_CLASS = False

def clean_text(html: str) -> str:
    """String lvl fixes--runs before parsing so entities aren't lost"""
    html = LINEBREAKS.sub("", html)
    html = COMMENT_REMOVE.sub("", html)
    html = NBSP.sub(" ", html)
    html = INVISIBLES_REMOVE.sub("", html)
    html = html.replace("\r\n", "\n").replace("\r", "\n")
    return html

def clean_chapter(raw: bytes) -> bytes:
    soup = BeautifulSoup(clean_text(raw.decode("utf-8")), "lxml-xml")
    
    #Remove all comments
    for c in soup.find_all(string=lambda s: isinstance(s,Comment)):
        c.extract()
    
    #Remove attributes
    for meta in soup.find_all("meta", {"name": META_NAMES_TO_REMOVE}):
        meta.decompose()

    if STRIP_ID_CLASS:
        for tag in soup.find_all(True):
            tag.attrs.pop("id", None)
            tag.attrs.pop("class", None)
            
    return soup.encode(formatter="minimal")
    
    
def add_unlisted_images(book, epub_path: str) -> None:
    """ebooklib only saves files listed in the book's manifest. Some epubs link
    to images that aren't listed there, so add those back in or they'd be lost."""
    with zipfile.ZipFile(epub_path) as z:
        container = ElementTree.fromstring(z.read("META-INF/container.xml"))
        rootfile = container.find(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile")
        opf_dir = posixpath.dirname(rootfile.get("full-path"))
        listed = {unquote(item.file_name) for item in book.get_items()}

        for name in z.namelist():
            media_type = mimetypes.guess_type(name)[0] or ""
            if not media_type.startswith("image/"):
                continue
            if opf_dir and not name.startswith(opf_dir + "/"):
                continue  # outside the book's content folder; can't be re-linked
            rel_name = posixpath.relpath(name, opf_dir) if opf_dir else name
            if rel_name in listed:
                continue
            book.add_item(epub.EpubItem(
                uid=f"img_{uuid.uuid4().hex[:8]}",
                file_name=rel_name,
                media_type=media_type,
                content=z.read(name),
            ))
            print(f"Kept unlisted image: {rel_name}")


book_file_name = input("Enter book file name: ").strip().strip('"').strip("'")
book = epub.read_epub(book_file_name)
add_unlisted_images(book, book_file_name)

for item in book.get_items_of_type(ITEM_DOCUMENT):
    # Use item.content (the original file), not item.get_content():
    # ebooklib's get_content() rebuilds the page and throws away <head>
    # (stylesheet links, <style>, fonts) and the <body> attributes.
    completely_clean_chapter = clean_chapter(item.content)
    item.set_content(completely_clean_chapter)
    # ebooklib calls get_content() again when saving, so make it return
    # our cleaned file as-is instead of rebuilding it.
    item.get_content = lambda default=None, c=completely_clean_chapter: c
    
for ns, tags in book.metadata.items():
    for tag, entries in tags.items():
        tags[tag] = [
            (value, attrs) for value, attrs in entries
            if dict(attrs or {}).get("name") not in META_NAMES_TO_REMOVE
        ]
    
    new_id = f"urn:uuid: {uuid.uuid4()}"
    book.set_identifier(new_id)

# Title = filename only, without any folder path or the .epub extension
book_title = os.path.splitext(os.path.basename(book_file_name))[0]
book.set_title(book_title)

# Save the cleaned copy next to the original
output_path = os.path.join(os.path.dirname(book_file_name), f"{book_title}_clean.epub")
epub.write_epub(output_path, book)
print(f"Saved {output_path}")
