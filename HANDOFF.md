# Handoff: Skjer i Ålesund

_State as of 20 Oct 2026._

## Goal
A public website listing what's on in Ålesund (concerts, standup, shows, kids' events, clubs, happenings), with ticket prices, that updates itself every day.

**Live:** https://pedersen2k.github.io/skjer-i-alesund/
**Repo:** https://github.com/Pedersen2k/skjer-i-alesund (owner: Pedersen2k)

## Current state
- 99 upcoming events (Oct 2026 – Mar 2027). Almost all have real prices.
- The page has these features:
  - Filters for time, category, venue and price, plus search.
  - Favourites ("Mine"), stored in the browser.
  - A light/dark toggle.
  - "Legg i kalender", "Del" and map links on each event.
  - A logo (a jugendstil gable above a wave), also used as the favicon and for link previews (`og-image.png`).
- GitHub Actions runs twice a day, at about 06:50 and 20:50 Norway time (winter time; one hour later in summer). It fetches the latest events and commits `data/events.json`. If anything changed, it redeploys Pages.
- If a run fails or returns warnings, the workflow opens a GitHub issue, which emails the owner. The issue is closed automatically once a later run succeeds.

## Key decisions
- **Static site + GitHub Pages + Actions.** It's free, and visitors don't need to log in. An earlier version was a Claude artifact backed by a database, but only signed-in Claude users could see its data. The daily Claude task that updated it (`trig_01UEPBzcKQrHz5XpXGLXK7qc`) is **disabled, not deleted**. That artifact (https://claude.ai/artifact/GqCPeYEgqsrcpUir5M7FHj) is no longer updated.
- **Data comes from Tikkio and Parken's site, not from search.**
  - Tikkio event pages list every ticket type with its price.
  - The "price" field in Tikkio's listing is often `0.00`, which means unknown, not free.
  - The shown price is the ordinary ticket. Up to two discounts go in the note.
- **Repeated performances are merged into one card**, for example the Løvenvold Christmas show, which has 20+ dates. The other dates and times go in the note.
- **Nothing is invented.** Events, dates and prices come only from a source. When sources disagree, the event gets `uncertain: true` and an explanation in the note.
- Ticketmaster, Eventim and TicketCo were considered and not used. Almost all Ålesund events are sold on Tikkio.

## Key files
| File | Purpose |
|---|---|
| `index.html` | The entire site (HTML/CSS/JS). Reads `data/events.json`. |
| `scripts/sync.py` | Fetches Tikkio and Parken, merges repeated shows, applies overrides, and writes `data/events.json`. |
| `data/events.json` | Generated. Don't edit by hand. |
| `data/manual.json` | Events with no automatic source (e.g. the julemarked). Edit by hand. |
| `data/overrides.json` | Per-event fixes to category, title, time or note. The key is the normalized title slug. |
| `.github/workflows/oppdater.yml` | Daily sync, commit, Pages deploy, and failure alerts. |
| `scripts/artifact_preview.py` | Builds a preview of the site that can be published as a Claude artifact. |

## Next steps
1. **GoatCounter:** create a free account and set `GOATCOUNTER` in `index.html` (line ~171). Until then, no visits are counted.
2. **More sources:** Sjøborg, Ålesunds Museum, Jugendstilsenteret and AaFK are only covered if they sell on Tikkio. Add a scraper or `manual.json` entries for them.
3. **Custom domain** (optional): e.g. `skjerialesund.no`, about 150 kr a year. Point DNS to GitHub Pages and set it in repo Settings → Pages.
4. **Permission:** before promoting the site widely, check Tikkio's terms or ask the venues. Always link to their ticket pages, as the site does now.
5. Optional: a form where organizers can submit their own events.

## Gotchas
- The Claude cloud environment blocks `*.github.io`. Claude can't open the live site, so test locally: `python3 -m http.server`.
- `www.` domains must be allowlisted separately in the environment's network settings.
- The bot commits every day, so run `git pull` before pushing.
