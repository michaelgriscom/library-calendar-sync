#!/usr/bin/env python3
"""Scrapes a LibraryCalendar.com site and pushes a combined ICS feed to GitHub."""

import base64
import logging
import os
import re
import time

import requests
from bs4 import BeautifulSoup

CALENDAR_URL = os.environ.get("CALENDAR_URL", "").rstrip("/")
CALENDAR_FILTERS = os.environ.get("CALENDAR_FILTERS", "")
REFRESH_INTERVAL = int(os.environ.get("REFRESH_INTERVAL", "3600"))
CALENDAR_NAME = os.environ.get("CALENDAR_NAME", "Library Events")
REQUEST_DELAY = float(os.environ.get("REQUEST_DELAY", "1.0"))

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
GITHUB_FILE_PATH = os.environ.get("GITHUB_FILE_PATH", "")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger(__name__)

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": "library-calendar-sync/1.0 (personal calendar feed)",
    }
)


def scrape_event_ids() -> list[str]:
    """Scrape event node IDs from the upcoming events listing."""
    ids: set[str] = set()
    page = 0

    while True:
        params = f"{CALENDAR_FILTERS}&page={page}" if CALENDAR_FILTERS else f"page={page}"
        url = f"{CALENDAR_URL}/events/list?{params}"
        log.info("Fetching listing page %d", page)
        resp = SESSION.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Find all event links matching /event/slug-NNNNN
        links = soup.find_all("a", href=re.compile(r"/event/.+-\d+$"))
        page_ids: set[str] = set()
        for link in links:
            match = re.search(r"-(\d+)$", link["href"])
            if match:
                page_ids.add(match.group(1))

        if not page_ids:
            break

        ids.update(page_ids)

        # Check for next page link
        next_link = soup.find("a", attrs={"rel": "next"}) or soup.find(
            "a", title=re.compile(r"next page", re.I)
        )
        if not next_link:
            next_link = soup.find("a", string=re.compile(r"Next|›"))
        if not next_link:
            break

        page += 1
        time.sleep(REQUEST_DELAY)

    log.info("Found %d unique events", len(ids))
    return sorted(ids)


def download_ics(node_id: str) -> str | None:
    """Download ICS data for a single event."""
    url = f"{CALENDAR_URL}/node/{node_id}/export.ics"
    try:
        resp = SESSION.get(url, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception:
        log.warning("Failed to download ICS for node %s", node_id, exc_info=True)
        return None


def build_combined_ics(event_ids: list[str]) -> str:
    """Download individual ICS files and merge into one calendar."""
    vevents: list[str] = []

    for i, node_id in enumerate(event_ids):
        ics_text = download_ics(node_id)
        if ics_text:
            match = re.search(
                r"(BEGIN:VEVENT.*?END:VEVENT)", ics_text, re.DOTALL
            )
            if match:
                vevents.append(match.group(1))

        if i < len(event_ids) - 1:
            time.sleep(REQUEST_DELAY)

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//library-calendar-sync//EN",
        f"X-WR-CALNAME:{CALENDAR_NAME}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    for vevent in vevents:
        lines.append(vevent)
    lines.append("END:VCALENDAR")

    return "\r\n".join(lines)


def push_to_github(content: str):
    """Push the ICS file to a GitHub repo via the Contents API."""
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # Get current file SHA (needed for updates)
    sha = None
    resp = requests.get(api_url, headers=headers, timeout=15)
    if resp.status_code == 200:
        sha = resp.json()["sha"]
    elif resp.status_code != 404:
        resp.raise_for_status()

    encoded = base64.b64encode(content.encode()).decode()
    body: dict = {
        "message": "Update library calendar feed",
        "content": encoded,
        "committer": {
            "name": "library-calendar-sync",
            "email": "noreply@library-calendar-sync",
        },
    }
    if sha:
        body["sha"] = sha

    resp = requests.put(api_url, headers=headers, json=body, timeout=30)
    resp.raise_for_status()

    if sha:
        log.info("Updated %s in %s", GITHUB_FILE_PATH, GITHUB_REPO)
    else:
        log.info("Created %s in %s", GITHUB_FILE_PATH, GITHUB_REPO)


def refresh():
    """Run a full scrape and push the ICS file to GitHub."""
    try:
        log.info("Starting refresh...")
        event_ids = scrape_event_ids()
        if not event_ids:
            log.warning("No events found, skipping")
            return

        ics_content = build_combined_ics(event_ids)
        event_count = ics_content.count("BEGIN:VEVENT")
        log.info("Built ICS with %d events", event_count)

        push_to_github(ics_content)
    except Exception:
        log.exception("Refresh failed")


def main():
    missing = []
    if not CALENDAR_URL:
        missing.append("CALENDAR_URL")
    if not GITHUB_TOKEN:
        missing.append("GITHUB_TOKEN")
    if not GITHUB_REPO:
        missing.append("GITHUB_REPO")
    if not GITHUB_FILE_PATH:
        missing.append("GITHUB_FILE_PATH")
    if missing:
        log.error("Required environment variables not set: %s", ", ".join(missing))
        raise SystemExit(1)

    while True:
        refresh()
        log.info("Next refresh in %ds", REFRESH_INTERVAL)
        time.sleep(REFRESH_INTERVAL)


if __name__ == "__main__":
    main()
