# Handoff: Skjer i Ålesund

_State as of 24 Oct 2026. Cinema page live; the new mobile filter menu is live and the owner has tested it on a phone (looks good). The cinema calendar bug was fixed. See Next steps._

## Goal
A public website listing what's on in Ålesund (concerts, standup, shows, kids' events, clubs, happenings, AaFK home matches), with ticket prices, that updates itself every day.

**Live:** https://pedersen2k.github.io/skjer-i-alesund/
**Repo:** https://github.com/Pedersen2k/skjer-i-alesund (owner: Pedersen2k)

## Current state
- About 110 upcoming events (Oct 2026 – Mar 2027). Almost all have real prices, except AaFK matches.
- The page has these features:
  - Filters for time, category, venue and price, plus search.
  - Favourites ("Mine"), stored in the browser.
  - A light/dark toggle.
  - "Legg i kalender", "Del" and map links on each event.
  - Visitor stats with GoatCounter (no cookies), code `skjer-i-alesund`: https://skjer-i-alesund.goatcounter.com
  - A "Sport" category with match cards for AaFK home matches (men and women): league and venue on top, home team, kick-off time and away team, then ticket link. Prices are not shown (see Next steps).
  - Search engine support: schema.org `Event` JSON-LD, built in `index.html` from `events.json`, and `sitemap.xml`. The site is added to Google Search Console (verification meta tag in `index.html`, sitemap submitted).
  - Static subpages from `scripts/pages.py` (built at every deploy into `_site/`, which is what Pages publishes): `i-dag/`, `denne-helgen/`, one per category (`konserter/`, `standup/`, `show/`, `barn-og-familie/`, `klubb/`, `happenings/`, `aafk-hjemmekamper/`), `scene/<venue>/` for venues with 3+ events, and `arrangement/<id>/` per event, each with its own title, description and JSON-LD. `sitemap.xml` (all of them) and `404.html` are generated too. "Del" on the front page now links to the event page, so shared links get a proper preview.
  - A weekly "Helgepost": every Thursday `.github/workflows/helgepost.yml` opens an issue (emails the owner) with ready-to-paste Facebook and Instagram text for the coming weekend, closing last week's. The Instagram image (`denne-helgen/helgen.png`, 1080×1350, Pillow + Bricolage/Figtree fonts downloaded in the workflow, DejaVu fallback) is built by `pages.py` at every deploy and is also the `og:image` for `denne-helgen/`. If the large layout can't fit everything it switches to one-line rows, and spills over to `helgen-2.png` etc. (an Instagram carousel); the issue shows all images.
  - Repeated shows now carry `moreShows` (later start times) in `events.json`, so "I dag", "Denne helgen" and the weekly post include a show on every day it plays. The front page's date filters still only use the first date.
  - A logo (a jugendstil gable above a wave), also used as the favicon and for link previews (`og-image.png`).
- GitHub Actions runs twice a day, at about 06:50 and 20:50 Norway time (winter time; one hour later in summer). It fetches the latest events and commits `data/events.json`. If anything changed, it redeploys Pages.
- If a run fails or returns warnings, the workflow opens a GitHub issue, which emails the owner. The issue is closed automatically once a later run succeeds.
- Alert and Helgepost issues are assigned to the repo owner (`--assignee "$GITHUB_REPOSITORY_OWNER"`). Issues opened by the Actions bot only email people watching the repo; assignment makes GitHub email the owner. Confirmed working on 22 Oct (issue #12).

## Key decisions
- **Static site + GitHub Pages + Actions.** It's free, and visitors don't need to log in. An earlier version was a Claude artifact backed by a database, but only signed-in Claude users could see its data. The daily Claude task that updated it (`trig_01UEPBzcKQrHz5XpXGLXK7qc`) is **disabled, not deleted**. That artifact (https://claude.ai/artifact/GqCPeYEgqsrcpUir5M7FHj) is no longer updated.
- **Data comes from Tikkio and Parken's site, not from search.**
  - Tikkio event pages list every ticket type with its price.
  - The "price" field in Tikkio's listing is often `0.00`, which means unknown, not free.
  - The shown price is the ordinary ticket. Up to two discounts go in the note.
- **Repeated performances are merged into one card**, for example the Løvenvold Christmas show, which has 20+ dates. The other dates and times go in the note.
- **Nothing is invented.** Events, dates and prices come only from a source. When sources disagree, the event gets `uncertain: true` and an explanation in the note.
- Ticketmaster and Eventim were considered and not used. Almost all Ålesund events are sold on Tikkio. TicketCo is only used by AaFK, and its prices are not fetched.
- **AaFK matches are included** as category `sport`. `fetch_aafk()` in `sync.py` reads the schedule pages on aafk.no (men's and women's) and keeps only matches at Color Line Stadion. The page layout (`tr.schedule__match`) is a scraping target: if aafk.no changes it, the workflow opens an issue.
- **Sjøborg is dropped.** It is in Ulsteinvik, not Ålesund.

## Key files
| File | Purpose |
|---|---|
| `index.html` | The entire site (HTML/CSS/JS). Reads `data/events.json`. |
| `scripts/sync.py` | Fetches Tikkio, Parken and AaFK, merges repeated shows, applies overrides, and writes `data/events.json`. |
| `data/events.json` | Generated. Don't edit by hand. |
| `data/manual.json` | Events with no automatic source (e.g. the julemarked). Edit by hand. |
| `data/overrides.json` | Per-event fixes to category, title, time or note. The key is the normalized title slug. |
| `.github/workflows/oppdater.yml` | Daily sync, commit, Pages deploy, and failure alerts. |
| `scripts/pages.py` | Builds `_site/`: the front page plus static subpages, `sitemap.xml` and `404.html`. Run on every deploy. |
| `scripts/helgepost.py` | Weekly post text (for the Helgepost issue) and the weekend image. |
| `.github/workflows/helgepost.yml` | Thursday Helgepost issue. Can also be run by hand. |
| `scripts/artifact_preview.py` | Builds a preview of the site that can be published as a Claude artifact. |

## Next steps
1. **Cinema: mobile review (partly done 24 Oct).** The owner has tried the cinema calendar on a phone: the month arrows were broken (panel closed on click) and are fixed. Still not reviewed: day tiles that scroll sideways (the owner dislikes sideways scrolling on mobile, so consider a wrapped grid), the 2-column poster grid under 400px and the front-page strip. The `kino/` page is live. `scripts/kino.py` fetches ODEON Ålesund for the next 21 days from Filmweb's GraphQL API (`https://movieinfoqs.filmweb.no/graphql`, `movieQuery.getCurrentMovies(date, location:"Ålesund", removePastShows:false)`; introspection works) and writes `data/kino.json`. If the API fails it falls back to today's programme embedded in Filmweb's HTML (a warning issue is opened). The cinema publishes about a week ahead, so days after that only hold a few special screenings. odeonkino.no itself is behind Cloudflare (403), so Filmweb is the source (bookings link straight to odeonkino.no). Poster images are hotlinked from `cdn.sanity.io` (allowed in the environment since 23 Oct; verified they render undistorted; each poster has a coloured fallback with the title).
   Decisions from the owner, 23 Oct: **poster wall only** (no list/"Kort" view); the intro line is just "Hva som går på ODEON Ålesund (Amfi Moa)."; the date picker is day tiles for the first 7 days plus a "Velg dato" button next to them; the calendar opens as a floating panel **over** the posters (never pushes them down); **no IMDb or Filmweb links or ratings** under the films (Filmweb's rating field is empty; IMDb needs an OMDb key; owner said no). The source credit line at the bottom of the page ("Program og plakater via Filmweb ...") is kept.
   Pieces: `kino/` page, CSS and JS in `pages.py` (`kino_page`, `KINO_JS`, `.k*` and `.film`/`.poster` styles), a strip in `index.html` (`#kinostrip`), `kino_line()` in `helgepost.py` (only prints when the weekend has shows), a "Hent kinoprogram" step in `oppdater.yml`. Cinema is deliberately not in the main list, "I dag" or category pages. Sold-out status is not in the source, so it is not shown. Not yet reviewed by the owner on a phone: day tiles scroll sideways, the calendar panel, the 2-column poster grid under 400px, the front-page strip.
2. **Bing Webmaster Tools:** the owner postponed it. A reminder is scheduled for 12 Nov 2026 in the earlier Claude session; if that doesn't reach them, remind them (bing.com/webmasters → import from Google Search Console).
3. **More sources:** Ålesunds Museum and Jugendstilsenteret (now vitimusea.no) are only covered if they sell on Tikkio. Allow `www.aalesundmuseum.no` and `www.vitimusea.no` in the environment, check if their programmes can be read, otherwise add `manual.json` entries from their own pages.
4. **AaFK prices:** They are in TicketCo (`aafk.ticketco.events`). Check in a new session whether those pages can be read (the domain was allowed late in the last session). If not, keep "Pris hos arrangør".
5. **Search Console:** The owner resubmitted the sitemap after the subpages went live (22 Oct). After a few days, check that the sitemap shows "Vellykket" and look at the Events report. The JSON-LD has only been tested in node, not in Google's Rich Results Test.
6. **Mobile check:** The match cards were only rendered at desktop width.
7. **Custom domain** (optional): e.g. `skjerialesund.no`, about 150 kr a year. Point DNS to GitHub Pages and set it in repo Settings → Pages.
8. **Permission:** before promoting the site widely, check Tikkio's terms or ask the venues. Always link to their ticket pages, as the site does now.
9. Optional: a form where organizers can submit their own events.

## Calendar subscription (23 Oct, on branch, not merged)
`build_ics()` in `pages.py` writes `kalender/alle.ics` and one `.ics` per category into `_site/` at every deploy (one VEVENT per day/show, from `occurrences()`; Europe/Oslo VTIMEZONE; refresh hint 12 h). Owner chose design D from `docs/kalenderforslag.html`: in `index.html`, `#subscribe` is a strip that shows only when exactly one category is selected ("Abonner på standup i kalenderen"), expanding to iPhone/Mac (`webcal://`), Google Calendar and copy link (`updateSubscribe()`, called from `render()`). Not tested on a real phone; no entry point when no category is chosen (consider design A, a button at the top, as a supplement).

## Mobile menu (24 Oct)
The sticky filter bar (`.controls`) used to be about 440 px tall at 320 px width. Owner chose design H (no sideways scrolling): on phones (max-width 640px) the bar is search + "★ Mine" on one line and a 2x2 grid of dropdowns (`#mwhen`, `#mcat`, `#venue`, `#price`), about 160 px tall, and it slides away when scrolling down and returns on a small scroll up. On wider screens the chips are unchanged; the dropdowns and chips share `state` through `syncFilters()`. The dropdown for category is single-select (the chips allow several). The other designs (A, B, C, D, E, F, G) are kept as interactive mockups in `docs/menyforslag.html` and `docs/menyforslag-2.html` (open in a browser; not published).

## Bug fixed 24 Oct: cinema calendar arrows
Clicking the month arrows in the `kino/` calendar closed the panel. `render()` replaces the panel's HTML, so the clicked arrow was already detached when the document-level "click outside" handler ran. The handler now ignores detached targets (`e.target.isConnected`) in `KINO_JS` in `pages.py`. Beyond 31 Oct the calendar only has a few special screenings, because Filmweb publishes about a week ahead; that is expected.

## Preferences from the owner (24 Oct)
- Dislikes sideways scrolling on mobile.
- Wants to see several design options as interactive mockups before deciding (see `docs/`), then picks one.
- Tests on the phone after a merge to `main`, so merge when asked and say how to bypass the cache (hard refresh or private tab).

## Gotchas
- The Claude cloud environment blocks `*.github.io`. Claude can't open the live site, so test locally: `python3 -m http.server`.
- `www.` domains must be allowlisted separately in the environment's network settings.
- Hosts such as `aafk.ticketco.events` must be allowed in the environment's network settings; a change may need a new session to apply.
- The bot commits every day, so run `git pull` before pushing.
- Merging to `main` triggers the deploy workflow. If its last step ("deploy-pages") fails with a Pages error, it is usually transient: re-run the failed job once (Actions → Re-run failed jobs).
- Playwright is not installed in the environment. A working local check: `npm i playwright-core` in a scratch folder and launch `executablePath: '/opt/pw-browsers/chromium'` against `python3 -m http.server -d _site`. Rebuilding `_site/` deletes the folder, so restart the server afterwards.
