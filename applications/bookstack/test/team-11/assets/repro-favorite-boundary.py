"""Reproduction: the top-4 favourite boundary makes a viewing record re-enter My Recently Viewed.

Usage:  python repro-favorite-boundary.py http://127.0.0.1:<port>
Requires a running BookStack instance with the seeded verified account (no third-party packages).
"""

import http.cookiejar
import json
import sys
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:3000").rstrip("/")
ACCOUNT = {"email": "bookstack_user@example.com", "password": "Password123!"}
BOOKS = [f"Probe-Fav-{index:02d}" for index in range(1, 7)]

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def call(path, payload=None, method=None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        BASE + path, data=data, method=method or ("POST" if data is not None else "GET"),
        headers={"Content-Type": "application/json"})
    with opener.open(request) as response:
        body = response.read()
    return json.loads(body) if body else {}


def snapshot():
    home = call("/api/home")
    return ([item["name"] for item in home["recentlyViewed"]],
            [f'{item["type"]}:{item["name"]}' for item in home["favoriteTop"]])


call("/api/auth/login", ACCOUNT)

for name in BOOKS:
    book = call("/api/books", {"name": name, "description": "probe", "tags": "probe"})
    call(f"/api/books/{book['id']}")  # opening the book records a view

ids = {book["name"]: book["id"] for book in call("/api/books")["books"]}
viewed, favorites = snapshot()
print("after viewing six books:")
print("  recentlyViewed:", viewed)
print("  favoriteTop:   ", favorites)

for name in BOOKS[:4]:
    call(f"/api/favorites/book/{ids[name]}", {}, "POST")
viewed, favorites = snapshot()
print("\nafter favouriting", ", ".join(BOOKS[:4]) + ":")
print("  recentlyViewed:", viewed)
print("  favoriteTop:   ", favorites)

call(f"/api/favorites/book/{ids[BOOKS[4]]}", {}, "POST")
viewed, favorites = snapshot()
print(f"\nafter favouriting {BOOKS[4]}:")
print("  recentlyViewed:", viewed)
print("  favoriteTop:   ", favorites)

first_returned = BOOKS[0] in viewed
print(f"\nEXPECTED: {BOOKS[0]} stays visible or stays absent consistently (viewing history unchanged).")
print(f"ACTUAL:   {BOOKS[0]} reappeared = {first_returned}")
sys.exit(1 if first_returned else 0)
