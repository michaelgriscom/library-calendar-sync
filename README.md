# library-calendar-sync

Scrapes events from a [LibraryCalendar.com](https://www.librarycalendar.com/) site and publishes a combined ICS feed to a GitHub-hosted static site (e.g. GitHub Pages, Cloudflare Pages) for calendar subscription.

## How it works

1. Periodically scrapes the "upcoming events" page (with optional filters)
2. Downloads each event's individual `.ics` export from the site
3. Merges them into a single ICS calendar feed
4. Pushes the ICS file to a GitHub repo via the Contents API
5. Your static site host (Cloudflare Pages, GitHub Pages, etc.) auto-deploys the updated file

## Quick start

```bash
docker run -d \
  -e CALENDAR_URL=https://example.librarycalendar.com \
  -e CALENDAR_FILTERS="age_groups[1]=1&branches[73]=73" \
  -e CALENDAR_NAME="My Library Events" \
  -e GITHUB_TOKEN=ghp_xxxxxxxxxxxx \
  -e GITHUB_REPO=username/my-website \
  -e GITHUB_FILE_PATH=public/files/calendar.ics \
  ghcr.io/michaelgriscom/library-calendar-sync:latest
```

Then subscribe in your calendar app using the public URL where your site serves the file.

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `CALENDAR_URL` | **Yes** | — | Base URL of the LibraryCalendar site (e.g. `https://example.librarycalendar.com`) |
| `GITHUB_TOKEN` | **Yes** | — | GitHub personal access token with `contents: write` on the target repo |
| `GITHUB_REPO` | **Yes** | — | Target repo in `owner/repo` format (e.g. `username/my-website`) |
| `GITHUB_FILE_PATH` | **Yes** | — | Path within the repo to write the ICS file (e.g. `public/files/calendar.ics`) |
| `CALENDAR_FILTERS` | No | *(none)* | URL query string filters (e.g. `age_groups[1]=1&branches[73]=73`) |
| `CALENDAR_NAME` | No | `Library Events` | Display name shown in calendar apps |
| `REFRESH_INTERVAL` | No | `43200` | Seconds between scrapes (default 12 hours) |
| `REQUEST_DELAY` | No | `1.0` | Seconds between individual HTTP requests (rate limiting) |
| `PUSH_URL` | No | *(none)* | URL to GET after each successful sync (e.g. Uptime Kuma push monitor) |

### Finding your filters

1. Go to your library's calendar page (e.g. `https://example.librarycalendar.com/events/month`)
2. Use the filter controls to select the age groups, branches, etc. you want
3. Copy the query string from the URL — everything after the `?`
4. Set that as `CALENDAR_FILTERS`

### GitHub token

Create a [fine-grained personal access token](https://github.com/settings/tokens?type=beta) with:
- **Repository access**: Only the target website repo
- **Permissions**: Contents → Read and write

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
      - GITHUB_TOKEN=ghp_xxxxxxxxxxxx
      - GITHUB_REPO=username/my-website
      - GITHUB_FILE_PATH=public/files/calendar.ics
```

## Subscribing in Apple Calendar

**On Mac:** File → New Calendar Subscription → enter your public URL

**On iPhone/iPad:** Settings → Calendar → Accounts → Add Account → Other → Add Subscribed Calendar → enter your public URL

## License

[MIT](LICENSE)
