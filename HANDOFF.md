# Handoff: Skjer i Ålesund

_State as of 23 Oct 2026. Cinema page built and published (multi-day); see Next steps 1._

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
1. **Cinema (live).** `scripts/kino.py` fetches ODEON Ålesund for the next 21 days from Filmweb's GraphQL API (`https://movieinfoqs.filmweb.no/graphql`, `movieQuery.getCurrentMovies(date, location:"Ålesund", removePastShows:false)`; introspection works), and writes `data/kino.json`. If the API fails it falls back to today's programme embedded in Filmweb's HTML (a warning issue is opened). The cinema publishes about a week ahead, so days beyond that only hold a few special screenings. odeonkino.no itself is behind Cloudflare (403). Poster images are hotlinked from `cdn.sanity.io` (blocked in the Claude environment, so never seen rendering from here; each poster has a coloured fallback with the title). Pieces: `kino/` page + CSS + JS in `pages.py` (day chips, "plakatvegg" toggle), a strip in `index.html` (`#kinostrip`), `kino_line()` in `helgepost.py` (only prints when the weekend has shows), a "Hent kinoprogram" step in `oppdater.yml`. Not in the main list, "I dag" or category pages, by design. Sold-out status is not in the source, so it is not shown.
2. **Bing Webmaster Tools:** the owner postponed it. A reminder is scheduled for 12 Nov 2026 in the earlier Claude session; if that doesn't reach them, remind them (bing.com/webmasters → import from Google Search Console).
3. **More sources:** Ålesunds Museum and Jugendstilsenteret (now vitimusea.no) are only covered if they sell on Tikkio. Allow `www.aalesundmuseum.no` and `www.vitimusea.no` in the environment, check if their programmes can be read, otherwise add `manual.json` entries from their own pages.
4. **AaFK prices:** They are in TicketCo (`aafk.ticketco.events`). Check in a new session whether those pages can be read (the domain was allowed late in the last session). If not, keep "Pris hos arrangør".
5. **Search Console:** The owner resubmitted the sitemap after the subpages went live (22 Oct). After a few days, check that the sitemap shows "Vellykket" and look at the Events report. The JSON-LD has only been tested in node, not in Google's Rich Results Test.
6. **Mobile check:** The match cards were only rendered at desktop width.
7. **Custom domain** (optional): e.g. `skjerialesund.no`, about 150 kr a year. Point DNS to GitHub Pages and set it in repo Settings → Pages.
8. **Permission:** before promoting the site widely, check Tikkio's terms or ask the venues. Always link to their ticket pages, as the site does now.
9. Optional: a form where organizers can submit their own events.

## Gotchas
- The Claude cloud environment blocks `*.github.io`. Claude can't open the live site, so test locally: `python3 -m http.server`.
- `www.` domains must be allowlisted separately in the environment's network settings.
- Hosts such as `aafk.ticketco.events` must be allowed in the environment's network settings; a change may need a new session to apply.
- The bot commits every day, so run `git pull` before pushing.
