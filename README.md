# Skjer i Ålesund

Konserter, standup, show og happenings i Ålesund, samlet på ett sted, med billettpriser.

## Slik fungerer det

- `index.html` er hele nettsiden. Den leser programmet fra `data/events.json`.
- `scripts/sync.py` henter Ålesund-arrangementer og billettpriser fra Tikkio og programmet til Parken kulturhus, og skriver `data/events.json`.
- GitHub Actions (`.github/workflows/oppdater.yml`) kjører skriptet hver morgen, lagrer endringene og publiserer siden på GitHub Pages.

## Legge til eller rette arrangementer

- **Arrangementer som ikke ligger på Tikkio eller hos Parken**: legg dem til i `data/manual.json`.
- **Parken-arrangementer i `manual.json`** (id `parken-<nr>-parken-kulturhus`, der nummeret står i Parken-lenken) brukes bare som reserve når Parken-siden ikke svarer. Når henteren får tak i arrangementet, vinner den.
- **Rette kategori, tittel, klokkeslett eller notat**: legg inn en overstyring i `data/overrides.json`. Nøkkelen er den normaliserte tittelen (små bokstaver, bindestrek i stedet for mellomrom). For Parken kan du også bruke `parken-<nr>` når to arrangementer har samme tittel, for eksempel Ålesund symfoniorkester.

Kategorier: `konsert`, `standup`, `show`, `barn`, `klubb`, `happening`.

## Kjøre lokalt

```sh
python3 scripts/sync.py        # oppdaterer data/events.json
python3 -m http.server         # åpne http://localhost:8000
```

Priser og datoer hentes fra arrangørenes billettsider og kan endres. Sjekk alltid hos arrangøren før du kjøper billett.
