# White-box test: Undo after deleting an archived note restores it to Notes instead of Archived

## 1. Method and design basis

**Method:** white-box (state-transition analysis of the delete / undo / archive flags).
**Source:** `frontend/app.js`

| Location | Code | Meaning |
| --- | --- | --- |
| `deleteNote` | `n.deleted = true; n.archived = false;` | Deleting clears the archive flag permanently |
| `deleteNote` (undo) | `n.deleted = false;` | Undo restores only the delete flag |
| `archiveNote` | `n.archived = true;` | Archiving sets the flag |
| `renderNoteCard` | `archived ? Unarchive : Archive` | Archived cards expose the "More options" menu, so **Delete Note is reachable from Archived** |

Design basis: the two flags (`deleted`, `archived`) form a 2×2 state space and delete/undo only restores one of
them, so the transition `Archived → deleted → undo` has no way back to the archived state.

## 2. Requirement reference

- **REQ-2.4** (Delete notes and recover through notification Undo): deletion moves the note to Trash and the
  notification offers "Undo", which recovers the **same** note.
- **REQ-2.5** (Inspect and empty Trash): Trash shows deleted notes separately from active notes.
- **REQ-2.6** (Archive notes and restore them to active Notes): "Clicking 'Archived'(role=button) displays
  archived notes separately from active notes; 'Unarchive {title}'(role=button) returns the chosen note to
  Notes." The only specified way for an archived note to return to Notes is the Unarchive action, and
  "Every transition addresses that note's business identity and remains observable after reload."

A note that was archived therefore has to come back to **Archived** when a deletion of it is undone; the
requirement does not allow a second, implicit path from Archived into Notes.

## 3. Difference from existing tests

- `baseline/REQ-2.4.*` deletes a note that sits in active Notes and checks the Trash + Undo behaviour there.
- `baseline/REQ-2.5.*` inspects and empties Trash; it never deletes a note that is currently archived.
- `baseline/REQ-2.6.*` archives and unarchives notes; it never deletes one while it is archived.
- This test exercises the **cross-list** transition (Archived → delete → Undo), which no existing test reaches
  and which is the only state where the missing `archived` restore is observable.

## 4. Preconditions

- Notes view open, clean workspace state (no notes are required by the requirement).
- Note title/content created through the UI in the same run.

## 5. Reproduction steps

1. `Take a note`, enter Title `Probe Archived Undo` and Content `Archived undo content`, click **Close**.
   The note appears in **Other notes**.
2. Click **Archive Probe Archived Undo** on the card. The note leaves **Other notes**.
3. Open **Archived** in the sidebar: the note is listed once under **Archived notes**.
4. On that card open **More options Probe Archived Undo** → **Delete Note**. The note disappears and the
   notification "Note deleted" shows with **Undo**.
5. Click **Undo**.
6. Inspect **Archived** and then **Notes** (and reload; the state is persisted).

Automated equivalent: `assets/repro-archived-undo.py <base-url>` (Playwright, Python).

## 6. Expected vs actual

**Expected:** after Undo the note is back under **Archived notes**, exactly once, with its content; it must not
appear in active **Other notes**, because only "Unarchive {title}" may move it there.

**Actual (measured):**

| Step | Archived notes | Other notes |
| --- | --- | --- |
| after Close | 0 | 1 |
| after Archive | 1 | 0 |
| after Delete Note | 0 | 0 |
| after Undo | **0** | **1** |

The note silently moved from Archived to Notes, so the archive list lost a note that was never unarchived.

## 7. Evidence

Console output of the reproduction script against the shipped implementation:

```text
created, in Other notes: 1
after archive, in Other notes: 0
in Archived notes: 1
deleted from Archived; in Archived notes: 0
after Undo -> in Archived notes: 0
after Undo -> in Other notes: 1
```

The reproduction script writes `after-undo.png` next to itself when it runs, so the screenshot can be regenerated on demand.

Code reference confirming the cause: `deleteNote` sets `n.archived = false` while the undo callback only
restores `n.deleted = false`, so the archive state is lost irreversibly.
