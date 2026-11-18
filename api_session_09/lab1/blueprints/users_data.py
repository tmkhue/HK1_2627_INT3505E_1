"""In-memory user data used by the lab API blueprints."""

USERS = {
    1: {
        "f": "Nguyen",
        "l": "An",
        "first_name": "Nguyen",
        "last_name": "An",
        "email": "nguyen.an@example.com",
    },
    2: {
        "f": "Tran",
        "l": "Binh",
        "first_name": "Tran",
        "last_name": "Binh",
        "email": "tran.binh@example.com",
    },
    3: {
        "f": "Le",
        "l": "Chi",
        "first_name": "Le",
        "last_name": "Chi",
        "email": "le.chi@example.com",
    },
}


def get_user(uid):
    """Return the user identified by *uid*, or ``None`` if it is missing."""
    return USERS.get(uid)
