#!/usr/bin/env python3
"""Scrapes a LibraryCalendar.com site and serves a combined ICS feed."""

import http.server
import logging
import os
import re
import threading
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

CALENDAR_URL = os.environ.get("CALENDAR_URL", "").rstrip("/")
CALENDAR_FILTERS = os.environ.get("CALENDAR_FILTERS", "")
REFRESH_INTERVAL = int(os.environ.get("REFRESH_INTERVAL", "3600"))
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/data")
PORT = int(os.environ.get("PORT", "8080"))
CALENDAR_NAME = os.environ.get("CALENDAR_NAME", "Library Events")
REQUEST_DELAY = float(os.environ.get("REQUEST_DELAY", "1.0"))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger(__name__)

ICS_FILE = Path(OUTPUT_DIR) / "calendar.ics"

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
        url = f"{CALENDAR_URL}/events/upcoming?{params}"
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
            # Also check for "Next ›" text
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


def refresh():
    """Run a full scrape and regenerate the ICS file."""
    try:
        log.info("Starting refresh...")
        event_ids = scrape_event_ids()
        if not event_ids:
            log.warning("No events found, skipping ICS generation")
            return

        ics_content = build_combined_ics(event_ids)
        ICS_FILE.parent.mkdir(parents=True, exist_ok=True)
        ICS_FILE.write_text(ics_content)
        log.info(
            "Wrote %s with %d events",
            ICS_FILE,
            ics_content.count("BEGIN:VEVENT"),
        )
    except Exception:
        log.exception("Refresh failed")


def refresh_loop():
    """Periodically refresh the ICS file."""
    while True:
        refresh()
        log.info("Next refresh in %ds", REFRESH_INTERVAL)
        time.sleep(REFRESH_INTERVAL)


class ICSHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/calendar.ics"):
            try:
                content = ICS_FILE.read_bytes()
                self.send_response(200)
                self.send_header(
                    "Content-Type", "text/calendar; charset=utf-8"
                )
                self.send_header(
                    "Content-Disposition",
                    'inline; filename="calendar.ics"',
                )
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                self.send_error(503, "Calendar not yet generated")
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        log.info(format, *args)


def main():
    if not CALENDAR_URL:
        log.error("CALENDAR_URL is required (e.g. https://example.librarycalendar.com)")
        raise SystemExit(1)

    thread = threading.Thread(target=refresh_loop, daemon=True)
    thread.start()

    server = http.server.HTTPServer(("0.0.0.0", PORT), ICSHandler)
    log.info("Serving on port %d", PORT)
    server.serve_forever()


if __name__ == "__main__":
    main()
