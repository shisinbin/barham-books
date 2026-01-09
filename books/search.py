import re
from django.db.models import Q
# import unicodedata - need to install this package, I think

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
    "author_last_exact": 45,
    "author_last_startswith": 30,
    "author_first_exact": 20,
    "author_first_startswith": 10,
    "multi_term_bonus": 15,
}

def normalise_query(query):
    """
    Normalize user input into searchable terms.
    - lowercase
    - strip punctuation
    - remove stopwords
    - strip plurals
    """
    query = query.lower()
    # query = query.unicodedata.normalize("NFKD", query)
    query = re.sub(r"[^\w\s]", " ", query)

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

    If allow_prefix=True, last term is treated as partial.
    """
    query_filter = Q()

    for term in terms[:-1]:
        forms = plural_forms(term)
        term_q = Q()

        for f in forms:
            term_q |= Q(title__icontains=f)
            term_q |= Q(author__first_name__iexact=f)
            term_q |= Q(author__last_name__iexact=f)

        query_filter &= term_q

    last = terms[-1]
    last_forms = plural_forms(last)
    last_q = Q()

    for f in last_forms:
        if allow_prefix:
            last_q |= Q(title__icontains=f)
            last_q |= Q(author__first_name__istartswith=f)
            last_q |= Q(author__last_name__istartswith=f)
        else:
            last_q |= Q(title__icontains=f)
            last_q |= Q(author__first_name__iexact=f)
            last_q |= Q(author__last_name__iexact=f)

    return query_filter & last_q


def score_book(book, terms):
    """Return relevance score for sorting results."""
    score = 0

    # Pre-process book data
    title = book.title.lower()
    title_words = re.findall(r"\w+", title)
    author_first = (book.author.first_name or "").lower()
    author_last = (book.author.last_name or "").lower()

    for term in terms:
        # Title-scoring
        if term in title_words:
            score += SCORING_WEIGHTS["title_exact_word"]
        if title.startswith(term):
            score += SCORING_WEIGHTS["title_startswith"]
        if term in title:
            score += SCORING_WEIGHTS["title_contains"]

        # Author-scoring
        if term == author_last:
            score += SCORING_WEIGHTS["author_last_exact"]
        elif author_last.startswith(term):
            score += SCORING_WEIGHTS["author_last_startswith"]

        if term == author_first:
            score += SCORING_WEIGHTS["author_first_exact"]
        elif author_first.startswith(term):
            score += SCORING_WEIGHTS["author_first_startswith"]

    # Multi-term bonus
    if len(terms) > 1:
        match_count = 0
        for term in terms:
            if term in title or term in author_first or term in author_last:
                match_count += 1

        score += match_count * SCORING_WEIGHTS["multi_term_bonus"]

    return score

def classify_match(book, terms):
    """Extract match features used for intent detection."""
    title = book.title.lower()
    title_words = set(re.findall(r"\w+", title))
    author_first = (book.author.first_name or "").lower()
    author_last = (book.author.last_name or "").lower()

    features = {
        "title_exact_words": 0,
        "title_startswith": False,
        "author_first": False,
        "author_last": False,
    }

    for term in terms:
        if term in title_words:
            features["title_exact_words"] += 1
        if title.startswith(term):
            features["title_startswith"] = True
        if term == author_first:
            features["author_first"] = True
        if term == author_last:
            features["author_last"] = True

    return features

def is_confident_redirect(book, terms):
    """Return True if query unambiguously targets this book."""
    f = classify_match(book, terms);
    
    if f['title_startswith']:
        return True
    elif (
        f['title_exact_words'] == 1 and
        (f['author_first'] or f['author_last'])
    ):
        return True
    elif f['author_first'] and f['author_last']:
        return True
    elif f['title_exact_words'] >= 2:
        return True
    else:
        return False


#  OLD SEARCH BEFORE FACTORING IN PLURALISATION
# def build_search_filter(terms, allow_prefix=False):
#     """
#     Build a Q object for searching books.

#     If allow_prefix=True, last term is treated as partial.
#     """
#     query_filter = Q()

#     for term in terms[:-1]:
#         query_filter &= (
#             Q(title__icontains=term) |
#             Q(author__first_name__iexact=term) |
#             Q(author__last_name__iexact=term)
#         )

#     last = terms[-1]

#     if allow_prefix:
#         query_filter &= (
#             Q(title__icontains=last) |
#             Q(author__first_name__istartswith=last) |
#             Q(author__last_name__istartswith=last)
#         )
#     else:
#         query_filter &= (
#             Q(title__icontains=last) |
#             Q(author__first_name__iexact=last) |
#             Q(author__last_name__iexact=last)
#         )

#     return query_filter