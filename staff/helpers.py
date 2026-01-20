import re
import os
import uuid
from django.conf import settings
from django.core.files.storage import default_storage

ISBN_RE = re.compile(r"isbn_(\d{10}|\d{13})")

def extract_isbns_from_ia(ia_list):
    if not ia_list:
        return []
    
    matches = []
    for item in ia_list:
        m = ISBN_RE.search(item)
        if m:
            matches.append(m.group(1))
    return matches

def choose_best_isbn(isbns):
    for i in isbns:
        if len(i) == 13:
            return i
    for i in isbns:
        if len(i) == 10:
            return i
    return ""

def format_book_title(title):
    # Define minor words to leave in lowercase (except the first word)
    minor_words = {'the', 'of', 'with', 'from', 'a', 'an', 'on', 'at', 'for', 'and', 'but', 'in', 'to', 'by', 'or', 'nor', 'as', 'so', 'yet', 'is'}

    words = title.split()

    # Capitalise first word
    # words[0] = words[0].capitalize()

    # Capitalize non-minor words and lowercase minor words
    for i in range(0, len(words)):
        word = words[i]

        # Skip words starting with a number
        if word[0].isdigit():
            continue

        # Skip words that are entirely uppercase
        if word.isupper():
            continue

        # Deal with hyphenated word
        if '-' in word:
            parts = word.split('-')
            words[i] = '-'.join(part.capitalize() for part in parts)
            continue

        # Deal with French d' elision
        if word.lower().startswith("d'"):
            words[i] = f"d'{word[2:].capitalize()}"
            continue

        # Deal with words starting with 'Mc' (could also do 'Mac'?)
        if word.lower().startswith('mc') and len(word) > 2:
            words[i] = f"Mc{word[2:].capitalize()}"
            continue

        # Capitalise the first word of a title regardless
        if i == 0:
            words[0] = word.capitalize()
            continue

        # Capitalise non-minor words and lowercase minor words
        if word.lower() in minor_words:
            words[i] = word.lower()
        else:
            words[i] = word.capitalize()

    # Rejoin the words into a single string
    formatted_title = ' '.join(words)

    def capitalize_after_symbols(title):
        # List of symbols to check for
        symbols = [': ', '& ', '/ ']
        for symbol in symbols:
            if symbol in title:
                initial, rest = title.split(symbol, 1)
                if rest and rest[0].isalpha():
                    # Rebuild the title with character after symbol capitalised
                    title = f"{initial}{symbol}{rest[0].upper()}{rest[1:]}"
        return title
    
    formatted_title = capitalize_after_symbols(formatted_title)

    # Handle titles with a colon
    # if ': ' in formatted_title:
        # initial, rest = formatted_title.split(': ', 1)
        # if rest and rest[0].isalpha():
        #     formatted_title = f"{initial}: {rest[0].upper()}{rest[1:]}"

    # Move starting 'The', 'A', or 'An' to the end
    if formatted_title.lower().startswith(('the ', 'a ', 'an ')):
        first_word, rest_of_title = formatted_title.split(' ', 1)
        formatted_title = f"{rest_of_title}, {first_word}"

    return formatted_title

def format_author_name(author_name):
    """
    Formats an author's name.
    For names like 'J.K. Rowling' or 'J R R Tolkien', combines initials into the first name.
    For regular names like 'John Adam George Smith', processes first, middle, and last names conventionally.
    """
    # Remove periods and normalize whitespace
    author_name = re.sub(r'\.', ' ', author_name).strip()
    names = author_name.split()
    
    if len(names) < 2:
        raise ValueError("Need to enter a first and last name for the author.")

    # Case 1: Initials-based names (e.g., "J R R Tolkien" -> "JRR Tolkien")
    if all(len(name) == 1 for name in names[:-1]):  # Check if all but the last are single characters
        first_name = ''.join(n.upper() for n in names[:-1])  # Combine all initials into the first name
        middle_name = ''  # No middle name for initials-based names
        if '-' in names[-1]:
            partials = names[-1].split('-')
            last_name = '-'.join(p.capitalize() for p in partials)
        else:
            last_name = names[-1].capitalize()
    else:
        # Case 2: Regular names (e.g., "John Adam George Alexander Smith")
        first_name = names[0].capitalize()
        middle_name = ' '.join(names[1:-1]).title() if len(names) > 2 else ''
        if '-' in names[-1]:
            partials = names[-1].split('-')
            last_name = '-'.join(p.capitalize() for p in partials)
        else:
            last_name = names[-1].capitalize()

    return " ".join((first_name, middle_name, last_name))


def save_temp_uploaded_file(uploaded_file, subdir="temp"):
    """
    Save an uploaded file into MEDIA_ROOT/<subdir>/ with a unique name.
    Returns (relative_path, url).
    """
    # Ensure temp directory exists
    temp_dir = os.path.join(settings.MEDIA_ROOT, subdir)
    os.makedirs(temp_dir, exist_ok=True)

    # Build a unique filename, keep extension
    base, ext = os.path.splitext(uploaded_file.name)
    unique_name = f"{uuid.uuid4().hex}{ext or '.jpg'}"
    relative_path = os.path.join(subdir, unique_name)

    # Save using Django storage backend
    saved_path = default_storage.save(relative_path, uploaded_file)

    # Public URL for previewing
    url = default_storage.url(saved_path)

    return saved_path, url