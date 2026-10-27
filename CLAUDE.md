# Skjer i Ålesund

Offentlig nettside med konserter, standup, show og happenings i Ålesund, med billettpriser. Statisk side på GitHub Pages som oppdateres hver andre time på dagtid av GitHub Actions. Brukeren snakker norsk: svar og skriv UI-tekst på norsk (bokmål).

Full oversikt over mål, beslutninger, filer, neste steg og fallgruver: @HANDOFF.md
Brukerrettet dokumentasjon (manual.json, overrides.json, varsling): @README.md

## Regler
- `data/events.json` er generert. Aldri rediger for hånd. Bruk `data/manual.json` og `data/overrides.json`.
- Ikke finn på arrangementer, datoer eller priser. Alt skal komme fra en kilde (Tikkio, Parken) eller `manual.json`. Ved uenighet mellom kilder: `uncertain: true` med forklaring i notatet.
- Boten committer hver dag: kjør `git pull` før `git push`.
- Test lokalt (`python3 scripts/sync.py`, `python3 -m http.server`). Miljøet blokkerer trolig den live siden (`kaskjerda.no`, tidligere `*.github.io`), så den kan ikke åpnes herfra.
- Hold `index.html` som én fil uten byggesteg.
- Den gamle Claude-artifacten «Skjer i Ålesund» er en forhåndsvisningskopi og oppdateres ikke automatisk.

## Vedlikehold av denne filen
Når en økt avsluttes med viktige endringer, oppdater «State as of» og «Next steps» i `HANDOFF.md`, ikke denne filen.
