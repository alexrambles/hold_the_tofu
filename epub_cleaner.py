import os
from ebooklib import epub, ITEM_DOCUMENT
import re
from bs4 import BeautifulSoup, Comment
import uuid


"""<!--
u:48c78dd1-63f8-453f-9e35-2d7db14bffbb
-->
meta name="opennovel:user_id"


content.opf
remove:
meta name="book-token"
dc:identifier id="BookId" opf:scheme="UUID"


toc.ncx

remove:
<meta name="dtb:uid" content="urn:uuid:48c78dd1-63f8-453f-9e35-2d7db14bffbb" />


all files:
replace any nbsp with space
replace any non visible spaces with ''

"""

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
    
    
book_file_name = input("Enter book file name: ").strip().strip('"').strip("'")   
book = epub.read_epub(book_file_name)

for item in book.get_items_of_type(ITEM_DOCUMENT):
    completely_clean_chapter = clean_chapter(item.get_content())
    item.set_content(completely_clean_chapter)
    
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
