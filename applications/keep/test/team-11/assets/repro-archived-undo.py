"""Reproduction: Undo after deleting an archived note restores it to Notes, not Archived.

Usage:  python repro-archived-undo.py http://127.0.0.1:<port>
Requires: Playwright for Python (pip install playwright && playwright install chromium).
"""

import sys
import time

from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:3000").rstrip("/")
TITLE = f"Probe Archived Undo {str(int(time.time()))[-6:]}"
CONTENT = "Archived undo content"


def count(page, region_name, note_title):
    return page.get_by_role("region", name=region_name, exact=True) \
               .get_by_role("region", name=note_title, exact=True).count()


with sync_playwright() as runtime:
    browser = runtime.chromium.launch()
    page = browser.new_page()
    page.set_default_timeout(6000)
    page.goto(BASE, wait_until="networkidle")

    page.get_by_role("button", name="Take a note", exact=True).click()
    page.get_by_label("Title", exact=True).fill(TITLE)
    page.get_by_label("Content", exact=True).fill(CONTENT)
    page.get_by_role("button", name="Close", exact=True).click()
    page.wait_for_timeout(400)
    print("created, in Other notes:", count(page, "Other notes", TITLE))

    page.get_by_role("button", name=f"Archive {TITLE}", exact=True).click()
    page.wait_for_timeout(400)
    page.get_by_role("button", name="Archived", exact=True).click()
    page.wait_for_timeout(400)
    print("in Archived notes:", count(page, "Archived notes", TITLE))

    page.get_by_role("button", name=f"More options {TITLE}", exact=True).click()
    page.get_by_role("menuitem", name="Delete Note", exact=True).click()
    page.wait_for_timeout(400)
    print("deleted from Archived; in Archived notes:", count(page, "Archived notes", TITLE))

    page.get_by_role("button", name="Undo", exact=True).click()
    page.wait_for_timeout(500)
    archived = count(page, "Archived notes", TITLE)
    page.get_by_role("button", name="Notes", exact=True).click()
    page.wait_for_timeout(400)
    active = count(page, "Other notes", TITLE)
    print("after Undo -> in Archived notes:", archived)
    print("after Undo -> in Other notes:", active)
    page.screenshot(path="after-undo.png", full_page=True)
    browser.close()

print("\nEXPECTED: the note returns to Archived notes (only Unarchive may move it to Notes).")
print(f"ACTUAL:   Archived={archived}, Notes={active}")
sys.exit(0 if archived == 1 and active == 0 else 1)
