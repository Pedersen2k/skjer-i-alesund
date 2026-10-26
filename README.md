# Skjer i Ålesund

Nettsiden ligger på https://kaskjerda.no/ (GitHub Pages med eget domene).

Konserter, standup, show og happenings i Ålesund, samlet på ett sted, med billettpriser.

## Slik fungerer det

- `index.html` er hele nettsiden. Den leser programmet fra `data/events.json`.
- `scripts/sync.py` henter Ålesund-arrangementer og billettpriser fra Tikkio, programmet til Parken kulturhus kalenderen til Dampsentralen (`dampsentralen.no/kalender?format=json`) og arrangementene til Viti (`vitimusea.no/arrangement`, bare de i Ålesund: Jugendstilsenteret og Sunnmøre museum), og skriver `data/events.json`. Dampsentralen har ikke priser på siden sin; er det en Tikkio-lenke i beskrivelsen, hentes prisen derfra.
- `scripts/pages.py` lager statiske undersider for søkemotorer og deling: «I dag», «Denne helgen», én side per kategori, per scene (med minst tre arrangementer) og per arrangement, pluss `sitemap.xml` og `404.html`. Alt legges i `_site/` (ikke i git) sammen med forsiden, og det er `_site/` som publiseres.
- `scripts/kino.py` henter kinoprogrammet til ODEON Ålesund fra Filmweb (odeonkino.no blokkerer roboter) og skriver `data/kino.json`. Kino holdes utenfor `events.json`, og vises på `kino/` og som en stripe på forsiden. Fjern det ved å slette kino-delene i `pages.py`, `index.html`, `helgepost.py` og workflowen.
- GitHub Actions (`.github/workflows/oppdater.yml`) kjører skriptet to ganger i døgnet (morgen og kveld), lagrer endringene og publiserer siden på GitHub Pages.

## Søkemotorer (SEO)

`scripts/pages.py` lager hele det søkemotorene trenger: forsiden får tittel med nøkkelord, de neste ukene som vanlig HTML (scriptet bytter dem ut når programmet er hentet) og JSON-LD (`WebSite`, `Organization`, `Event`). Undersidene (i dag, i morgen, denne helgen, neste 7 dager, måneder, kategorier, scener og ett arrangement hver) har egne titler, beskrivelser, brødsmuler (`BreadcrumbList`) og korte datadrevne tekster. Dessuten lages `robots.txt`, `sitemap.xml`, `manifest.webmanifest` og ikonene. `scripts/indexnow.py` sier fra til Bing m.fl. etter hver publisering (Google henter sitemapet selv).

## Jul i Ålesund

`jul-i-alesund/` (bygget av `jul_page()` i `scripts/pages.py`) er en sesongside med adventskalender og liste. Julearrangementer finnes automatisk: ord i tittel eller notat som begynner på jul, advent, nøtteknekk, lucia, romjul, nisse eller tomte. Rett opp med `data/jul.json` (`include` og `exclude` med arrangement-id). Julekortet på forsiden vises av JavaScript bare fra 1. november til 26. desember (legg til `?jul=1` i adressen for å se det utenom sesongen), og «Jul i Ålesund» kommer i snarveiene fra 1. november.

## Helgepost

Hver torsdag formiddag lager workflowen `.github/workflows/helgepost.yml` et issue med tittelen «Helgepost: …», så du får det på e-post. Det inneholder en ferdig tekst til Facebook-grupper, en bildetekst til Instagram og helgebildet (1080 × 1350), som ligger på `denne-helgen/helgen.png` og også er forhåndsvisningen når noen deler `denne-helgen/`. Er det mange arrangementer, blir linjene kompakte, og får heller ikke det plass, fortsetter lista på `helgen-2.png` osv., som du legger ut som karusell. Forrige ukes helgepost lukkes automatisk. Du kan lage en når som helst under Actions → Helgepost → Run workflow. Teksten og bildet lages av `scripts/helgepost.py`.

## Varsling og statistikk

- **Varsling:** Feiler morgenoppdateringen, svarer ikke Parken, eller faller antall arrangementer kraftig, lager jobben et issue med tittelen «Programoppdateringen trenger tilsyn», og GitHub sender deg e-post. Nye problemer legges til som kommentarer i samme issue. Det lukkes automatisk neste morgen alt går fint. Siden viser også selv et varsel hvis programmet er mer enn tre dager gammelt.
- **Statistikk:** Siden teller besøk med [GoatCounter](https://www.goatcounter.com), som ikke bruker informasjonskapsler. Statistikken ligger på https://kaskjerda.goatcounter.com (eldre tall fra før domenet ligger på https://skjer-i-alesund.goatcounter.com), og koden står i `GOATCOUNTER` øverst i skriptet i `index.html`. I tillegg til sidevisninger telles trykk på billettlenker, kart, kalender, deling, lagring og filtre (aldri hva folk søker etter).

## Legge til eller rette arrangementer

- **Arrangementer som ikke ligger på Tikkio eller hos Parken**: legg dem til i `data/manual.json`.
- **Parken-arrangementer i `manual.json`** (id `parken-<nr>-parken-kulturhus`, der nummeret står i Parken-lenken) brukes bare som reserve når Parken-siden ikke svarer. Når henteren får tak i arrangementet, vinner den.
- **Rette kategori, tittel, klokkeslett eller notat**: legg inn en overstyring i `data/overrides.json`. Nøkkelen er den normaliserte tittelen (små bokstaver, bindestrek i stedet for mellomrom). For Parken kan du også bruke `parken-<nr>` når to arrangementer har samme tittel, for eksempel Ålesund symfoniorkester.

Kategorier: `konsert`, `standup`, `show`, `barn`, `klubb`, `happening`.

## Forhåndsvisning i Claude

`python3 scripts/artifact_preview.py` lager `preview/` (ikke i git), som publiseres til artefakten «Skjer i Ålesund» på claude.ai for å se designendringer før de merges. Artefakten er bare en kopi: den oppdateres ikke av seg selv, og «Legg i kalender» virker ikke der.

## Kjøre lokalt

```sh
python3 scripts/sync.py        # oppdaterer data/events.json
python3 scripts/pages.py       # lager _site/ med undersider
python3 -m http.server -d _site   # åpne http://localhost:8000
```

Priser og datoer hentes fra arrangørenes billettsider og kan endres. Sjekk alltid hos arrangøren før du kjøper billett.
