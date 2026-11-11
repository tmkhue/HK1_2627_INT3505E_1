"""LAB 1 — add your five tests here. Do not delete the smoke tests.

A. GET /books, empty database -> HTTP 200 and []
B. GET /books/9999 -> HTTP 404, JSON code == NOT_FOUND
C. POST /books with only author -> HTTP 400, errors contains title
D. POST valid book, DELETE it, GET same id -> HTTP 404
BONUS. Validate a Book response using JSON Schema; add an unknown
       field to a *copy* of the response and assert ValidationError.

Useful imports:
    from jsonschema import validate, ValidationError
    import pytest
    from tools import get_book_schema
Do not depend on test execution order. Fixtures: client, app, sample_book.
"""
from jsonschema import validate, ValidationError
import pytest
from tools import get_book_schema

def test_list_books_empty(client):
    response = client.get("/books")

    assert response.status_code == 200
    assert response.get_json() == []


def test_get_missing_book_returns_not_found(client):
    response = client.get("/books/9999")

    assert response.status_code == 404
    assert response.get_json()["code"] == "NOT_FOUND"


def test_create_book_requires_title(client):
    response = client.post("/books", json={"author": "J.J. Geewax"})

    assert response.status_code == 400
    assert any(item["field"] == "title" for item in response.get_json()["errors"])


def test_created_book_can_be_deleted(client):
    create_response = client.post(
        "/books",
        json={"title": "API Design Patterns", "author": "J.J. Geewax"},
    )
    book_id = create_response.get_json()["id"]

    delete_response = client.delete(f"/books/{book_id}")
    get_response = client.get(f"/books/{book_id}")

    assert create_response.status_code == 201
    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_response_extra_field_blocked(client, sample_book):
    response = client.get(f"/books/{sample_book}")
    book = response.get_json()
    schema = get_book_schema()

    assert response.status_code == 200
    assert "password_hash" not in book
    validate(book, schema)
    response_with_password_hash = book.copy()
    response_with_password_hash["password_hash"] = "must-not-be-exposed"

    with pytest.raises(ValidationError):
        validate(response_with_password_hash, schema)