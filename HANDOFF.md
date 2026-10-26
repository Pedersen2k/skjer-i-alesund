# Handoff: Skjer i Ålesund

_State as of 26 Oct 2026. Live at kaskjerda.no with: calendar subscription and calendar view, SEO work, Jul i Ålesund page (front-page card appears 1 Nov), Dampsentralen as a source, new GoatCounter account. See Next steps and Open decisions._

## Goal
A public website listing what's on in Ålesund (concerts, standup, shows, kids' events, clubs, happenings, AaFK home matches), with ticket prices, that updates itself every day.

**Live:** https://kaskjerda.no/ (the old https://pedersen2k.github.io/skjer-i-alesund/ redirects there)
**Repo:** https://github.com/Pedersen2k/skjer-i-alesund (owner: Pedersen2k)

## Current state
- About 110 upcoming events (Oct 2026 – Mar 2027). Almost all have real prices, except AaFK matches.
- The page has these features:
  - Filters for time, category, venue and price, plus search.
  - Favourites ("Mine"), stored in the browser.
  - A light/dark toggle.
  - "Legg i kalender", "Del" and map links on each event.
  - Visitor stats with GoatCounter (no cookies), code `kaskjerda`: https://kaskjerda.goatcounter.com (before 26 Oct the code was `skjer-i-alesund`, old stats stay at https://skjer-i-alesund.goatcounter.com)
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
7. **Custom domain `kaskjerda.no` (live since 24 Oct; Search Console verified).** GitHub Pages DNS check passed. `BASE` in `scripts/pages.py`, `og:url`/`og:image`/canonical in `index.html`, the Helgepost image footer and a `CNAME` file in `_site/` now use `kaskjerda.no`. DNS zone at the registrar: four A records for `@` (185.199.108.153, .109.153, .110.153, .111.153), CNAME `www` → `pedersen2k.github.io`; MX/TXT untouched. Remaining for the owner: tick **Enforce HTTPS** in Settings → Pages (when available); Search Console: add `kaskjerda.no` as a new property, verify (the verification meta tag is already in `index.html`), submit `https://kaskjerda.no/sitemap.xml`; Bing Webmaster Tools at the same time. GoatCounter is unchanged. Optional: buy `skjerialesund.no` and 301-forward it. The site name stays "Skjer i Ålesund"; "Ka skjer da?" is only the address.
8. **Permission:** before promoting the site widely, check Tikkio's terms or ask the venues. Always link to their ticket pages, as the site does now.
9. Optional: a form where organizers can submit their own events.

## Calendar subscription (23 Oct, live; owner confirmed it works on iPhone)
`build_ics()` in `pages.py` writes `kalender/alle.ics` and one `.ics` per category into `_site/` at every deploy (one VEVENT per day/show, from `occurrences()`; Europe/Oslo VTIMEZONE; refresh hint 12 h). Owner chose design D from `docs/kalenderforslag.html`: in `index.html`, `#subscribe` is a strip that shows only when exactly one category is selected ("Abonner på standup i kalenderen"), expanding to iPhone/Mac (`webcal://`), Google Calendar and copy link (`updateSubscribe()`, called from `render()`). Not tested on a real phone; no entry point when no category is chosen (consider design A, a button at the top, as a supplement).

## Calendar view (23 Oct, live; owner approved the design after testing on phone)
`index.html` has a "Liste | Kalender" switch (`#viewseg`, remembered in localStorage as `skjer-view`). Calendar = month grid with one coloured dot per event and the selected day's events below (`renderCal()`, `.mc-*` styles). It uses the same filters as the list except the date filter (hidden via `.kalmode`), and counts `moreShows` dates. Owner chose month + day list only; a week view (mockups in `docs/visningsforslag.html`, `docs/kalender-kombinert.html`) can be added later if GoatCounter `kalender-visning/*` shows use.

## Mobile menu (24 Oct)
The sticky filter bar (`.controls`) used to be about 440 px tall at 320 px width. Owner chose design H (no sideways scrolling): on phones (max-width 640px) the bar is search + "★ Mine" on one line and a 2x2 grid of dropdowns (`#mwhen`, `#mcat`, `#venue`, `#price`), about 160 px tall, and it slides away when scrolling down and returns on a small scroll up. On wider screens the chips are unchanged; the dropdowns and chips share `state` through `syncFilters()`. The dropdown for category is single-select (the chips allow several). The other designs (A, B, C, D, E, F, G) are kept as interactive mockups in `docs/menyforslag.html` and `docs/menyforslag-2.html` (open in a browser; not published).

## Bug fixed 24 Oct: cinema calendar arrows
Clicking the month arrows in the `kino/` calendar closed the panel. `render()` replaces the panel's HTML, so the clicked arrow was already detached when the document-level "click outside" handler ran. The handler now ignores detached targets (`e.target.isConnected`) in `KINO_JS` in `pages.py`. Beyond 31 Oct the calendar only has a few special screenings, because Filmweb publishes about a week ahead; that is expected.

## Ideas discussed for getting traffic (not started)
- Add a line about the calendar subscription to the Helgepost text (`helgepost.py`).
- Draft emails to venues (Parken, Løvenvold, Terminalen) asking them to link to the site, and ask permission to use their data (see Next steps 8); QR poster text; press tips (Sunnmørsposten, Radio Møre, Visit Ålesund).
- Weekly newsletter (e.g. Buttondown) built from the Helgepost text.
- Design A from `docs/kalenderforslag.html` (small calendar button in the top bar) as an entry point for everyone, if GoatCounter shows few people use the category strip (`kalender/*` events).
- Week view for the calendar, only if `kalender-visning/*` shows use.
- More sources (museum, Jugendstilsenteret), AaFK prices, a form for organizers.

## SEO work (25 Oct, live)
Done in `scripts/pages.py` and `index.html`: keyworded front page title/description; the next 45 days pre-rendered as HTML into `#list` (JS replaces it; the first `render()` is skipped when `#list` already has content) and `WebSite` + `Organization` + `Event` JSON-LD (`#ld-front`; the client-side JSON-LD is skipped when it exists); new pages `i-morgen/`, `denne-uka/`, `maned/<måned>-<år>/` (months with 6+ events); `BreadcrumbList` on every page; short data-driven `facts` text and category/venue intro text (`CAT_TEXT`); free events get `isAccessibleForFree`; `robots.txt`, `manifest.webmanifest`, real PNG icons (`favicon-48.png`, `icon-192/512.png`, `apple-touch-icon.png`, made once from the logo SVG with headless Chromium), robots meta with `max-image-preview:large`; IndexNow (`scripts/indexnow.py`, key in `pages.INDEXNOW_KEY`, workflow step with `continue-on-error`). The new IndexNow step and the Pages build are untested in Actions.
Owner to-do (outside the repo): Search Console → request indexing for `/`, `/denne-helgen/`, `/konserter/`, `/standup/`; check the Events report in a week; get links from venues, Visit Ålesund, local groups (links matter more than anything else now); once social profiles exist, add them as `sameAs` in the `Organization` JSON-LD.

## Poster and social media mockups (25 Oct, in `docs/`, owner has not chosen)
- `docs/plakatforslag.html`: four A4 poster designs (Ka skjer da? / Kjeder du deg i kveld? / Hva skal du i helgen? / tear-off tabs), each with its own QR code to `https://kaskjerda.no/?ref=plakat-...` (GoatCounter shows the `ref`). No events on the posters, so they never go out of date. Owner has not chosen.
- `docs/sosiale-medier.html`: six social post designs with ready captions, built from real events of 26 Oct – 1 Nov: brand post, "Uka i tall", Halloween, "Fra 100 kr", story "I kveld", A/B poll. The generators are in the session scratchpad (not in the repo). Owner wants "something cool for social media" more than posters; natural next step is a script like `helgepost.py` that renders the chosen ones automatically from `events.json` and posts them in a weekly issue.
Both are also published as private Claude artifacts (owner has the links in the chat).

## Jul i Ålesund mockups (26 Oct)
`docs/jul-forslag.html`: five designs for a seasonal page `jul-i-alesund/` (A countdown, B advent calendar, C ticket style, D practical filtered list, E "what kind of Christmas?" tiles), built from the 9 real Christmas events found by keywords (`jul`, `nøtteknekk`, `advent`). Owner chose B (advent calendar as gift boxes) with D (filtered list) underneath, cozier: see `docs/jul-b-d.html` (string lights, falling snow, ribbon-wrapped days with events, Fraunces serif, cream/green/red). Front page entry mockups: `docs/jul-forside.html` (1 Christmas strip like the cinema strip, 2 card with mini calendar, 3 header pill + chip + footer link; all seasonal, 1 Nov – 26 Dec). Owner has seen them; chosen: pending. When built: add a `jul` tag/keyword rule in `pages.py` (and optionally a `tags` field in `manual.json`), generate the page with `listing_page`-style static HTML, add it to the sitemap and the nav, and publish it in November. Other ideas from the same chat: "Foreslå et arrangement" form (GitHub issue form), "Handle lokalt" page (needs owner-supplied shops, nothing invented), data-driven pages (gratis/billig, etter kl. 21).

## Jul i Ålesund page (26 Oct, live; front-page card and nav chip appear 1 Nov)
Owner chose the card on the front page (design 2) and wants it shown from 1 Nov; the page itself can be live earlier so Google finds it. `jul_page()` in `pages.py` builds `jul-i-alesund/` (gift-box advent calendar, filtered list, static HTML for SEO, JS enhancements; CSS in `SUB_CSS` as `.jul ...`), found by `is_jul()` (prefix rule + `data/jul.json` include/exclude). Front page card `#julcard` is in `index.html` and shown by JS from 1 Nov to 26 Dec (`?jul=1` forces it). `links_nav` gets a "Jul i Ålesund" chip from 1 Nov (`JUL_NAV`). A reminder for 1 Nov is scheduled (trigger `trig_01M4pGjdgNWkPnNm81NtUJgy`). To do each week in Nov/Dec: ask Claude to check for Christmas events that the keyword rule misses (Lucia, julemarkeder, small shops via `manual.json`).

## Dampsentralen as a source (26 Oct)
Owner asked that events from dampsentralen.no are always included. `fetch_dampsentralen()` in `sync.py` reads `https://www.dampsentralen.no/kalender?format=json` (Squarespace; `upcoming` list), venue `Dampsentralen` (no address in the source), category from `guess_cat()` plus entries in `overrides.json` (`circus-damp`, `inkluderingskveld-2026`, `christmas-party`). Repeated "KLUBB DAMP" Saturdays are merged into one card with `moreShows`. If a description links to a Tikkio event, prices come from there; otherwise "Pris hos arrangør". If the page can't be read, the old Dampsentralen events are kept and a warning issue is opened. The domain `www.dampsentralen.no` had to be allowed in the environment's network settings (done by the owner). `christmas-party-dampsentralen` is in `data/jul.json` `include`.

## Open decisions and to-do (end of session 26 Oct)
- **Workflow gap (important):** `oppdater.yml` skips the sync step on `push`, so after merging a change to `sync.py`, overrides or a new source, the data is NOT refreshed until the next scheduled run. Start it with `actions_run_trigger` (`run_workflow`, `oppdater.yml`, ref `main`) right after merging. The owner has been offered to change the workflow so pushes also sync (no loop: the bot's push uses GITHUB_TOKEN); not decided.
- **Reminders scheduled:** 1 Nov 09:00 about Jul i Ålesund and missing Christmas events (`trig_01M4pGjdgNWkPnNm81NtUJgy`); 12 Nov for Bing Webmaster Tools. Neither can send a phone push.
- **Owner has not chosen yet:** poster designs (`docs/plakatforslag.html`), social post designs (`docs/sosiale-medier.html`; wants "something cool for social media", natural next step is a script that renders them from `events.json` and puts them in a weekly issue).
- **Not started:** "Foreslå et arrangement" (GitHub issue form), "Handle lokalt" page (needs shops from the owner, nothing invented), data-driven pages (gratis/billig, etter kl. 21), newsletter, Helgepost line about calendar subscription, outreach email drafts (venues, Visit Ålesund, press; given in chat only, ask again if needed).
- **Owner to-do outside the repo:** Search Console sitemap + request indexing (`/`, `/jul-i-alesund/`, `/denne-helgen/`, `/konserter/`, `/standup/`), Enforce HTTPS, Bing import, links from venues; test `?jul=1` on the phone.
- **Dampsentralen:** "KLUBB DAMP 2.JULEDAG" is set to 26 Dec by override (`date` + `fromDate`), their calendar says 19 Dec.
- **Lessons:** never `pkill -f` a pattern that matches the running shell (kills the session shell); when resetting the working branch from `origin/main`, don't force-push over unmerged branch commits; the stop hook wants the branch pushed, committing `data/events.json` from a local sync is not wanted (the bot regenerates it).

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
