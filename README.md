# library-calendar-sync

Scrapes events from a [LibraryCalendar.com](https://www.librarycalendar.com/) site and serves a combined ICS feed that can be subscribed to from Google Calendar, Apple Calendar, Outlook, etc.

## How it works

1. Periodically scrapes the "upcoming events" page (with optional filters)
2. Downloads each event's individual `.ics` export from the site
3. Merges them into a single ICS calendar feed
4. Serves it over HTTP for calendar apps to subscribe to

## Quick start

```bash
docker run -d \
  -e CALENDAR_URL=https://example.librarycalendar.com \
  -e CALENDAR_FILTERS="age_groups[1]=1&branches[73]=73" \
  -e CALENDAR_NAME="My Library Events" \
  -p 8080:8080 \
  ghcr.io/michaelgriscom/library-calendar-sync:latest
```

Then subscribe in your calendar app using `http://localhost:8080/calendar.ics`.

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `CALENDAR_URL` | **Yes** | — | Base URL of the LibraryCalendar site (e.g. `https://example.librarycalendar.com`) |
| `CALENDAR_FILTERS` | No | *(none)* | URL query string filters (e.g. `age_groups[1]=1&branches[73]=73`) |
| `CALENDAR_NAME` | No | `Library Events` | Display name shown in calendar apps |
| `REFRESH_INTERVAL` | No | `3600` | Seconds between scrapes |
| `REQUEST_DELAY` | No | `1.0` | Seconds between individual HTTP requests (rate limiting) |
| `PORT` | No | `8080` | HTTP server port |
| `OUTPUT_DIR` | No | `/data` | Directory to write the generated ICS file |

### Finding your filters

1. Go to your library's calendar page (e.g. `https://example.librarycalendar.com/events/month`)
2. Use the filter controls to select the age groups, branches, etc. you want
3. Copy the query string from the URL — everything after the `?`
4. Set that as `CALENDAR_FILTERS`

## Docker Compose

```yaml
services:
  library_calendar_sync:
    image: ghcr.io/michaelgriscom/library-calendar-sync:latest
    restart: unless-stopped
    environment:
      - CALENDAR_URL=https://example.librarycalendar.com
      - CALENDAR_FILTERS=age_groups[1]=1&branches[73]=73
      - CALENDAR_NAME=My Library Events
```

## Subscribing in Google Calendar

1. Go to [Google Calendar](https://calendar.google.com)
2. Click the **+** next to "Other calendars" → **From URL**
3. Paste the URL to your running instance (e.g. `https://librarycal.example.com/calendar.ics`)
4. Click **Add calendar**

Google Calendar refreshes subscribed calendars roughly every 12–24 hours.

## Endpoints

| Path | Description |
|---|---|
| `/` or `/calendar.ics` | The combined ICS feed |
| `/health` | Health check (returns `200 ok`) |

## License

[MIT](LICENSE)
