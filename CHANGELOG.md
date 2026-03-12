# Changelog

## [0.2.0](https://github.com/michaelgriscom/library-calendar-sync/compare/v0.1.0...v0.2.0) (2026-03-12)


### Features

* add event URLs to calendar event descriptions ([153c73b](https://github.com/michaelgriscom/library-calendar-sync/commit/153c73b9e27306a8c8cb56e30a3d17e5330e0711)), closes [#2](https://github.com/michaelgriscom/library-calendar-sync/issues/2)
* merge ROOM into LOCATION for proper calendar display ([14cfdb4](https://github.com/michaelgriscom/library-calendar-sync/commit/14cfdb4b1702e43c5d53bec15c56fab6c4c99379))


### Bug Fixes

* keep raw street address in LOCATION, drop non-standard ROOM ([9c58c9e](https://github.com/michaelgriscom/library-calendar-sync/commit/9c58c9e66e498b0e1b9771e13f4c3f2b7ecb182a))

## 0.1.0 (2026-03-12)


### Features

* add README, LICENSE, and remove hardcoded defaults ([92e66dd](https://github.com/michaelgriscom/library-calendar-sync/commit/92e66ddcb273d841252107d4cdeb6f8d64e8b27c))
* initial library calendar to ICS sync service ([4a961ca](https://github.com/michaelgriscom/library-calendar-sync/commit/4a961ca2b1a655c5d9c871432a851b6780030a0d))
* push ICS to GitHub repo instead of serving over HTTP ([2235672](https://github.com/michaelgriscom/library-calendar-sync/commit/22356728b719c24f2d5d4c5bc31582accb4dc727))


### Bug Fixes

* create /data directory with correct ownership in image ([9f77407](https://github.com/michaelgriscom/library-calendar-sync/commit/9f77407e500a1f003d4aba9cbeb068667242bedb))
* opt into Node.js 24 for GitHub Actions ([a25012a](https://github.com/michaelgriscom/library-calendar-sync/commit/a25012a31ac2ee9f2bdf49c738b5356f473670fc))
* use /events/list endpoint instead of /events/upcoming ([4a2031f](https://github.com/michaelgriscom/library-calendar-sync/commit/4a2031fb28c563d8d397e00a9fa2267d4c5c29fb))
