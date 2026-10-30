# Skjer i Ålesund

Nettsiden ligger på https://kaskjerda.no/ (GitHub Pages med eget domene).

Konserter, standup, show og happenings i Ålesund, samlet på ett sted, med billettpriser.

## Slik fungerer det

- `index.html` er hele nettsiden. Den leser programmet fra `data/events.json`.
- `scripts/sync.py` henter Ålesund-arrangementer og billettpriser fra Tikkio, programmet til Parken kulturhus kalenderen til Dampsentralen (`dampsentralen.no/kalender?format=json`) arrangementene til Viti (`vitimusea.no/arrangement`, bare de i Ålesund: Jugendstilsenteret og Sunnmøre museum) programmet til Fabrikken Kulturscene (`fabrikkenkulturscene.no/program`) og arrangementene og DJ-planen til Liv & Røre på Amfi Moa (`livrore.no`), og skriver `data/events.json`. Dampsentralen har ikke priser på siden sin; er det en Tikkio-lenke i beskrivelsen, hentes prisen derfra. Fabrikken selger billetter på Billetto; prisen vises bare når den står på Fabrikkens egen side (foreløpig bare julebordet).
- `scripts/pages.py` lager statiske undersider for søkemotorer og deling: «I dag», «Denne helgen», én side per kategori, per scene (med minst tre arrangementer) og per arrangement, pluss `sitemap.xml` og `404.html`. Alt legges i `_site/` (ikke i git) sammen med forsiden, og det er `_site/` som publiseres.
- `scripts/kino.py` henter kinoprogrammet til ODEON Ålesund fra Filmweb (odeonkino.no blokkerer roboter) og skriver `data/kino.json`. Kino holdes utenfor `events.json`, og vises på `kino/` og som en stripe på forsiden. Fjern det ved å slette kino-delene i `pages.py`, `index.html`, `helgepost.py` og workflowen.
- GitHub Actions (`.github/workflows/oppdater.yml`) kjører skriptet hver andre time fra ca. kl. 06 til 22, lagrer endringene og publiserer siden på GitHub Pages.

## Søkemotorer (SEO)

`scripts/pages.py` lager hele det søkemotorene trenger: forsiden får tittel med nøkkelord, de neste ukene som vanlig HTML (scriptet bytter dem ut når programmet er hentet) og JSON-LD (`WebSite`, `Organization`, `Event`). Undersidene (i dag, i morgen, denne helgen, neste 7 dager, måneder, kategorier, scener og ett arrangement hver) har egne titler, beskrivelser, brødsmuler (`BreadcrumbList`) og korte datadrevne tekster. Dessuten lages `robots.txt`, `sitemap.xml`, `manifest.webmanifest` og ikonene. `scripts/indexnow.py` sier fra til Bing m.fl. etter hver publisering (Google henter sitemapet selv).

## Jul i Ålesund

`jul-i-alesund/` (bygget av `jul_page()` i `scripts/pages.py`) er en sesongside med adventskalender og liste. Julearrangementer finnes automatisk: ord i tittel eller notat som begynner på jul, advent, nøtteknekk, lucia, romjul, nisse eller tomte. Rett opp med `data/jul.json` (`include` og `exclude` med arrangement-id). Julekortet på forsiden vises av JavaScript bare fra 1. november til 26. desember (legg til `?jul=1` i adressen for å se det utenom sesongen), og «Jul i Ålesund» kommer i snarveiene fra 1. november.

## Julebord

Kategorien `julebord` er for julebord som alle kan bestille (ikke selskapslokaler for store grupper). Den vises på forsiden bare når programmet har julebord, og har egen side `julebord/`. Tittel med «julebord», «julebuffet» eller «julegilde» blir julebord automatisk. Julebord på hoteller og båter uten billettside ligger i `data/manual.json` med lenke til kilden. Julemenyer på restaurant uten faste datoer står i `data/julebord.json` og vises i en egen boks på `julebord/`. Sjekk begge hver høst.

## Helgepost

Hver torsdag formiddag lager workflowen `.github/workflows/helgepost.yml` et issue med tittelen «Helgepost: …», så du får det på e-post. Det inneholder en ferdig tekst til Facebook-grupper, en bildetekst til Instagram og helgebildet (1080 × 1350), som ligger på `denne-helgen/helgen.png` og også er forhåndsvisningen når noen deler `denne-helgen/`. Er det mange arrangementer, blir linjene kompakte, og får heller ikke det plass, fortsetter lista på `helgen-2.png` osv., som du legger ut som karusell. Forrige ukes helgepost lukkes automatisk. Du kan lage en når som helst under Actions → Helgepost → Run workflow. Teksten og bildet lages av `scripts/helgepost.py`.

## Varsling og statistikk

- **Varsling:** Feiler oppdateringen, svarer ikke Parken, eller faller antall arrangementer kraftig, lager jobben et issue med tittelen «Programoppdateringen trenger tilsyn», og GitHub sender deg e-post. Nye problemer legges til som kommentarer i samme issue (samme problem som sist gir ingen ny kommentar). Det lukkes automatisk neste gang alt går fint. Siden viser også selv et varsel hvis programmet er mer enn tre dager gammelt.
- **Statistikk:** Siden teller besøk med [GoatCounter](https://www.goatcounter.com), som ikke bruker informasjonskapsler. Statistikken ligger på https://kaskjerda.goatcounter.com (eldre tall fra før domenet ligger på https://skjer-i-alesund.goatcounter.com), og koden står i `GOATCOUNTER` øverst i skriptet i `index.html`. I tillegg til sidevisninger telles trykk på billettlenker, kart, kalender, deling, lagring og filtre (aldri hva folk søker etter).

## Lagre siden

En knapp «Lagre» øverst (bokmerkeikon) og en melding etter første ★ ber folk ta siden med seg. Android og Chrome/Edge på PC får en ekte «Installer»-knapp, iPhone får veiledning (Del, Legg til på Hjem-skjerm), andre PC-nettlesere får Ctrl/Cmd+D. Koden heter `SAVE` i `index.html`. Boksen og meldingen skjules når siden er åpnet som app, og «Nei takk» huskes i nettleseren.

## Utsolgt og «Få billetter igjen»

`sync.py` leser merket på hver Tikkio-side («Utsolgt» / «Få billetter igjen») og statusen hos Parken (hele arrangementet og hver forestilling). Oversikten til Tikkio sier alltid «på lager», så det er merket på selve siden som teller. Kortet får et lite «Få billetter igjen»-merke, og har arrangementet 2–6 forestillinger, vises tidene som knapper med status («13:00 utsolgt», «18:00 få igjen»). Parken merker nesten alt, så deres merke vises bare de siste to ukene før forestillingen.

## Juletema

`tema-jul.css` er et juletema for forsiden: mørk fløyelsrød med gull, en adventskrans der lysene tennes søndagene i advent, og en nisse som titter over julekortet. Det brukes for alle fra 1. november til 27. desember og slår seg av av seg selv etterpå. «Lyst» gjelder hele året. Utenom sesongen kan du se det med `?tema=jul` (bare i den fanen). Undersidene beholder kveldstemaet. Vil du fjerne det før tiden, endre datoene i temalasteren øverst i `index.html`. Forslagene det ble valgt fra ligger i `docs/jul-design/`.

## Delingsbilde per arrangement

Hver arrangementsside får sitt eget forhåndsbilde (1200 × 630, `arrangement/<id>/deling.jpg`), som vises når lenken deles på Messenger, Facebook, SMS, WhatsApp osv. Bildet har kategori, tittel, dato, sted, pris eller status (utsolgt, få igjen, gratis) og Ålesund-silhuetten, med snø og hvit måne fra 30. oktober til og med februar og uten snø (gyllen måne) resten av året (`winter()`). Det lages av `scripts/delingsbilde.py` ved hver publisering (trenger Pillow og skriftene, som helgebildet). Adressen har `?v=` som endres når innholdet endres, så Facebook henter nytt bilde når for eksempel et arrangement blir utsolgt. Mangler Pillow, brukes logoen som før.

## Engelsk side

`en/` (bygget av `en_page()` i `scripts/pages.py`) er «What's on in Ålesund» for turister og andre som søker på engelsk: de neste 14 dagene dag for dag, «In town for the day?» og «Good to know». Titlene står som hos arrangøren; datoer, kategorier, priser og forklaringer er på engelsk. Norsk og engelsk forside peker på hverandre med `hreflang`, og en knapp «English» (jordklode, «EN» på mobil) står ved «Mørkt | Lyst» øverst til høyre. På den engelske siden står «Norsk» på samme sted.

## Legge til eller rette arrangementer

- **Arrangementer som ikke ligger på Tikkio eller hos Parken**: legg dem til i `data/manual.json`.
- **Parken-arrangementer i `manual.json`** (id `parken-<nr>-parken-kulturhus`, der nummeret står i Parken-lenken) brukes bare som reserve når Parken-siden ikke svarer. Når henteren får tak i arrangementet, vinner den.
- **Rette kategori, tittel, klokkeslett eller notat**: legg inn en overstyring i `data/overrides.json`. Nøkkelen er den normaliserte tittelen (små bokstaver, bindestrek i stedet for mellomrom). For Parken kan du også bruke `parken-<nr>` når to arrangementer har samme tittel, for eksempel Ålesund symfoniorkester.

Kategorier: `konsert`, `standup`, `show`, `barn`, `klubb`, `happening`, `quiz`, `julebord`, `sport`.

## Forhåndsvisning i Claude

`python3 scripts/artifact_preview.py` lager `preview/` (ikke i git), som publiseres til artefakten «Skjer i Ålesund» på claude.ai for å se designendringer før de merges. Artefakten er bare en kopi: den oppdateres ikke av seg selv, og «Legg i kalender» virker ikke der.

## Kjøre lokalt

```sh
python3 scripts/sync.py        # oppdaterer data/events.json
python3 scripts/pages.py       # lager _site/ med undersider
python3 -m http.server -d _site   # åpne http://localhost:8000
```

Priser og datoer hentes fra arrangørenes billettsider og kan endres. Sjekk alltid hos arrangøren før du kjøper billett.
