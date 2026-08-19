import re
import unicodedata

from django.db.models import Q

# STOPWORDS = [
#     "the", "and", "for", "with", "from", "that",
#     "this", "into", "onto", "over", "under",
#     "about", "after", "before", "between",
#     "through", "without", "within", "upon",
#     "book", "books", "novel", "novels", "story", "stories"
# ]

STOPWORDS = ["the", "and", "for"]

SCORING_WEIGHTS = {
    "title_exact_word": 50,
    "title_startswith": 40,
    "title_contains": 20,
    "author_last_exact_word": 45,
    "author_last_contains": 28,
    "author_first_exact": 20,
    "author_first_startswith": 10,
    "author_middle_exact_word": 16,
    "author_middle_contains": 8,
    "multi_term_bonus": 15,
}

def normalise_text(value):
    """
    Normalise text for search comparisons.

    - lowercase
    - strip accents
    - replace punctuation with spaces
    - collapse repeated whitespace
    """
    value = value or ""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value

def normalise_query(query):
    """
    Normalize user input into searchable terms.
    """
    query = normalise_text(query)

    terms = []
    for word in query.split():
        if len(word) >= 3 and word not in STOPWORDS:
            terms.append(word)

    return terms

def plural_forms(term):
    """
    Return possible plural variants for matching

    Assumptions:
    - term is lowercase
    - term length >= 3
    - punctuation already stripped
    """
    forms = {term}

    # parties -> party
    if term.endswith("ies"):
        base = term[:-3] + "y"
        if len(base) >= 3:
            forms.add(base)
            return forms

    # boxes -> box, wishes -> wish, catches -> catch
    if term.endswith("es") and term[:-2].endswith(("sh", "ch", "x", "s")):
        base = term[:-2]
        if len(base) >= 3:
            forms.add(base)
            return forms

    # dogs -> dog (not dress -> dres)
    if term.endswith("s") and not term.endswith("ss"):
        base = term[:-1]
        if len(base) >= 3:
            forms.add(base)
            return forms

    # party -> parties
    if term.endswith("y") and term[-2] not in "aeiou":
        forms.add(term[:-1] + "ies")
        return forms
    
    # glass -> glasses
    if term.endswith("ss"):
        forms.add(term + "es")
        return forms

    # default plural
    forms.add(term + "s")
    return forms

def build_search_filter(terms, allow_prefix=False):
    """
    Build a Q object for searching books.

    Each term must match somewhere useful:
    - title
    - author first name
    - author middle names
    - author last name

    Author last names are treated as phrase-like fields so 'carre'
    can match 'le Carré' and 'jawaheri' can match 'Al-jawaheri'.

    If allow_prefix=True, last term is treated as partial.
    """
    query_filter = Q()

    for index, term in enumerate(terms):
        is_last = index == len(terms) - 1
        term_q = Q()

        # Title matching keeps plural variants.
        for form in plural_forms(term):
            term_q |= Q(title__unaccent__icontains=form)

        # Author names should use the original term, not plural variants.
        if allow_prefix and is_last:
            term_q |= Q(author__first_name__unaccent__istartswith=term)
            term_q |= Q(author__middle_names__unaccent__icontains=term)
            term_q |= Q(author__last_name__unaccent__icontains=term)
        else:
            term_q |= Q(author__first_name__unaccent__iexact=term)
            term_q |= Q(author__middle_names__unaccent__icontains=term)
            term_q |= Q(author__last_name__unaccent__icontains=term)

        query_filter &= term_q

    return query_filter

def score_book(book, terms):
    """Return relevance score for sorting results."""
    score = 0

    title = normalise_text(book.title)
    title_words = set(title.split())

    author = book.author
    author_first = normalise_text(author.first_name if author else "")
    author_middle = normalise_text(author.middle_names if author else "")
    author_last = normalise_text(author.last_name if author else "")

    author_first_words = set(author_first.split())
    author_middle_words = set(author_middle.split())
    author_last_words = set(author_last.split())

    author_full = " ".join(
        part for part in [author_first, author_middle, author_last] if part
    )

    for term in terms:
        # Title scoring
        if term in title_words:
            score += SCORING_WEIGHTS["title_exact_word"]

        if title.startswith(term):
            score += SCORING_WEIGHTS["title_startswith"]

        if term in title:
            score += SCORING_WEIGHTS["title_contains"]

        # Author last-name scoring
        if term in author_last_words:
            score += SCORING_WEIGHTS["author_last_exact_word"]
        elif term in author_last:
            score += SCORING_WEIGHTS["author_last_contains"]

        # Author first-name scoring
        if term in author_first_words:
            score += SCORING_WEIGHTS["author_first_exact"]
        elif author_first.startswith(term):
            score += SCORING_WEIGHTS["author_first_startswith"]

        # Author middle-name scoring
        if term in author_middle_words:
            score += SCORING_WEIGHTS["author_middle_exact_word"]
        elif term in author_middle:
            score += SCORING_WEIGHTS["author_middle_contains"]

    if len(terms) > 1:
        match_count = 0

        for term in terms:
            if term in title or term in author_full:
                match_count += 1

        score += match_count * SCORING_WEIGHTS["multi_term_bonus"]

    return score

def classify_match(book, terms):
    """Extract match features used for intent detection."""
    title = normalise_text(book.title)
    title_words = set(title.split())

    author = book.author
    author_first = normalise_text(author.first_name if author else "")
    author_middle = normalise_text(author.middle_names if author else "")
    author_last = normalise_text(author.last_name if author else "")

    author_first_words = set(author_first.split())
    author_middle_words = set(author_middle.split())
    author_last_words = set(author_last.split())

    features = {
        "title_exact_words": 0,
        "title_startswith": False,
        "author_first": False,
        "author_middle": False,
        "author_last": False,
    }

    for term in terms:
        if term in title_words:
            features["title_exact_words"] += 1

        if title.startswith(term):
            features["title_startswith"] = True

        if term in author_first_words:
            features["author_first"] = True

        if term in author_middle_words:
            features["author_middle"] = True

        if term in author_last_words:
            features["author_last"] = True

    return features

def is_confident_redirect(book, terms):
    """Return True if query unambiguously targets this book."""
    f = classify_match(book, terms)

    if f["title_startswith"]:
        return True

    if (
        f["title_exact_words"] == 1 and
        (f["author_first"] or f["author_middle"] or f["author_last"])
    ):
        return True

    if f["author_first"] and f["author_last"]:
        return True

    if f["title_exact_words"] >= 2:
        return True

    return False