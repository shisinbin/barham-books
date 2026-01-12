FAKE_REVIEWS = [
    {
        "title": "A brilliant read",
        "body": "I couldn't put this book down.\nHighly recommended.",
        "rating": 5,
        "user": {
            "username": "booklover92",
        },
    },
    {
        "title": "Enjoyable but flawed",
        "body": "Some parts were slow, but overall a good story.",
        "rating": 3,
        "user": {
            "username": "casual_reader",
        },
    },
]

FAKE_COPIES = [
    {
        "status": "a",
        "get_status_display": "Available",
        "isbn10": "0123456789",
        "get_formatted_isbn10": "0-123-45678-9",
        "isbn13": "0123456789012",
        "get_formatted_isbn13": "012-34-56789-01-2",
        "pages": 100,
        "book_type": True,
        "get_book_type_display": "Paperback",
    },
    {
        "status": "o",
        "get_status_display": "On loan",
        "due_back": "Christmas 3026",
        "borrower": {
            "username": "MrLoverLover"
        },
        "isbn13": "0123456789012",
        "get_formatted_isbn13": "012-34-56789-01-2",
        "pages": 200,
        "book_type": True,
        "get_book_type_display": "Hardcover",
    },
    {
        "status": "r",
        "get_status_display": "Reserved",
        "isbn10": "0123456789",
        "get_formatted_isbn10": "0-123-45678-9",
        "isbn13": "0123456789012",
        "get_formatted_isbn13": "012-34-56789-01-2",
        "pages": 300,
        "book_type": True,
        "get_book_type_display": "Paperback",
    }
]