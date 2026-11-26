# White-box test: the top-4 favourite boundary makes a viewing record leave and re-enter My Recently Viewed

## 1. Method and design basis

**Method:** white-box (statement + boundary analysis on the filter that feeds the dashboard).
**Source:** `backend/src/slices/bookstack.ts`, `/api/home` handler.

| Block | Lines | Code | Effect |
| --- | --- | --- | --- |
| 4 | 217–222 | `const favoriteTop = favorites.slice(0, 4);`<br>`const favoriteKeys = new Set(favoriteTop.map(...))` | The filter key set is built from **at most four** favourites |
| 5 | 223–229 | `recentlyViewed.filter(item => !favoriteKeys.has(...))` | Any record whose key is in that set is dropped from `recentlyViewed` |

Because `favoriteKeys` derives from `favoriteTop`, the set changes when a **newer** favourite pushes an
older one out of the top four. Design basis: boundary value on `slice(0, 4)` combined with the filter in
block 5 — the same unchanged viewing record is filtered in one run and kept in the next.

## 2. Requirement reference

- **REQ-3.1** (Authenticated dashboard): the authenticated homepage exposes the named regions
  "My Recent Drafts", "My Recently Viewed", "My Most Viewed Favorites" and "Recently Updated Pages".
- **REQ-7 / REQ-7.1** (Recently viewed): opening content records a visit and the region "contains at
  most ten records and opens the selected item. The source does not define a tie-breaker or eviction
  order." Nothing in the source ties membership to the favourite state or to the favourite ordering.
- **REQ-8.2** (Homepage favourites): favourited content appears under "My Most Viewed Favorites"; the
  requirement does not make the two regions mutually exclusive.

## 3. Difference from existing tests and from the TA demonstration

- `baseline/REQ-7.1.spec.ts` visits a shelf and asserts that it appears in recently viewed; it never
  favourites it.
- `baseline/REQ-8.1.spec.ts` / `REQ-8.2.spec.ts` create favourites and assert the favourites region;
  they never assert the effect on recently viewed.
- The TA demonstration (`FOLLOWING.md` §6–7) covers **one** favourite: the target leaves recently viewed.
- This test covers the **fifth favourite**, i.e. the `slice(0, 4)` boundary: the record that had already
  left the region **comes back** when a newer favourite displaces it. The additional behaviour covered is
  the interaction between block 4's limit and block 5's filter, which no existing test exercises.

## 4. Preconditions

- Fresh BookStack instance, logged out first.
- Verified account: `bookstack_user@example.com` / `Password123!` (nickname `BookStack User`).
- Six identifiable books (`Probe-Fav-01` … `Probe-Fav-06`) created in the same run, each opened once so a
  viewing record exists, and **no** favourites yet.

## 5. Reproduction steps

Through the interface (identical state machine, slower to set up):

1. Log in with the verified account; confirm "My Recently Viewed" is present.
2. `Books → Create New Book`, save `Probe-Fav-01` … `Probe-Fav-06`; saving opens each new book, so all six
   get a viewing record.
3. From `Books`, open `Probe-Fav-01` … `Probe-Fav-04` and press **Favorite** on each.
   *Observed so far:* the four favourited books leave "My Recently Viewed" (the defect the TA demonstrated).
4. Open `Probe-Fav-05` and press **Favorite**.
   *Observed:* `Probe-Fav-05` leaves the region **and `Probe-Fav-01` reappears in it**, although its
   viewing record never changed and it is still favourited.
5. Refresh the homepage: the state is stable (not a rendering race).

Automated equivalent (API level, deterministic; recommended for the TA):
`assets/repro-favorite-boundary.py` — start the application, then run
`python assets/repro-favorite-boundary.py http://127.0.0.1:<port>`.

## 6. Expected vs actual

**Expected:** membership of "My Recently Viewed" depends only on the viewing history (at most ten records,
no requirement-defined eviction). A favourited book must not disappear, and must certainly not reappear
because a *different* book was favourited later.

**Actual:** membership follows `favoriteTop`, which holds only four items:

| Step | Recently viewed (observed) | Favourites (observed) |
| --- | --- | --- |
| after six views | 06, 05, 04, 03, 02, 01 | — |
| after favouriting 01–04 | 06, 05 | 04, 03, 02, 01 |
| after favouriting 05 | 06, **01** | 05, 04, 03, 02 |

`Probe-Fav-01` is hidden in one state and visible in the next while its viewing record is unchanged and it
is still favourited in both states.

## 7. Evidence

Console output of the reproduction script:

```text
login: {'user': {'id': 1, 'nickname': 'BookStack User', 'email': 'bookstack_user@example.com'}}
created and viewed: ['Probe-Fav-01', 'Probe-Fav-02', 'Probe-Fav-03', 'Probe-Fav-04', 'Probe-Fav-05', 'Probe-Fav-06']
recentlyViewed: ['Probe-Fav-06', 'Probe-Fav-05', 'Probe-Fav-04', 'Probe-Fav-03', 'Probe-Fav-02', 'Probe-Fav-01']
favoriteTop: []

after favoriting the first four:
  recentlyViewed: ['Probe-Fav-06', 'Probe-Fav-05']
  favoriteTop: ['book:Probe-Fav-04', 'book:Probe-Fav-03', 'book:Probe-Fav-02', 'book:Probe-Fav-01']

after favoriting the fifth (Probe-Fav-05):
  recentlyViewed: ['Probe-Fav-06', 'Probe-Fav-01']
  favoriteTop: ['book:Probe-Fav-05', 'book:Probe-Fav-04', 'book:Probe-Fav-03', 'book:Probe-Fav-02']

05 still in recentlyViewed: False
04 still in recentlyViewed: False
```

Server log of the same request (block 5 diagnostic, abbreviated):

```text
[BookStack white-box][5] Filtered recently viewed records {
"beforeCount": 6,
"afterCount": 2,
"recentWithoutFavoriteDuplicates": [
{ "type": "book", "id": 6, "name": "Probe-Fav-06", ... },
{ "type": "book", "id": 1, "name": "Probe-Fav-01", ... }
],
"removedItems": [
{ "type": "book", "id": 5, "name": "Probe-Fav-05", ... },
{ "type": "book", "id": 4, "name": "Probe-Fav-04", ... },
...
```

`removedItems` contains exactly the four keys of `favoriteKeys`, which confirms that the removed set is
`favoriteTop` and not the full favourite collection.

## 8. Why this is not a duplicate

The demonstration and this test exercise different paths of the same filter: the demonstration shows that a
**favourite** is removed; this test shows that a record that left the region earlier (a book that is still
favourited) is **restored** when `slice(0, 4)` drops it from the key set. The observable difference is a
state change in the opposite direction (`1 → 0 → 1`) triggered by *another* book's favourite action, which
neither the baseline tests nor the demonstration cover.
