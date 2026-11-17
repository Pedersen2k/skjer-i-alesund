# Handoff: Skjer i Ålesund

Kort oversikt. All detaljert historikk (beslutninger, forslag som ikke ble valgt, testnotater per dato) ligger i `docs/HANDOFF-arkiv.md`: søk der (`grep`) ved behov, ikke les hele filen.

## State as of 17 Nov 2026 (kveld)
- Live på https://kaskjerda.no/ (repo: Pedersen2k/skjer-i-alesund). Ca. 150 kommende arrangementer.
- Sync hver andre time 06–22 (`oppdater.yml`, også på push til main). Varsler kommer som GitHub-issues til eieren.
- Instagram-poster som lages automatisk som issues: Helgepost (tors), «Helga i ett sveip» (`panorama.yml`, tors kveld), «Under hundrelappen» (søn) og «Uka i Ålesund» (man) via `ukepost.yml`. Ukepost-workflowen er bare prøvd for hånd; første planlagte kjøringer er 22.–23. nov.
- 17 Nov: «I kveld»-historie hver morgen (`ikveld.yml`, `scripts/ikveld.py`, variant G «Hemmelig liste» med farge etter ukedag; forslag i `docs/ikveld-historie/`). Erstatter dagsbildene i «Uka i Ålesund». Lenke `kaskjerda.no/i-dag/?ref=ig-story`: sjekk «ig-story» i GoatCounter om 2–3 uker (30 dager før start: ig ~15, Facebook ~6, Google ~500 besøk).
- Alle forsøk fra 1. nov (I kveld-linja, stjerne S4, overgang O3, tom liste T7) er permanente.
- 17 Nov: Bypatrioten krediteres bare for opplysninger som ikke står hos arrangøren (se CLAUDE.md). Jazzsirkelen og AaUM har mistet kreditten; Ålesund Filmklubb har bare pris/dørtid/medlemspris igjen fra Bypatrioten.

## Filer
| Fil | Hva |
|---|---|
| `index.html` | Hele forsiden (HTML/CSS/JS), leser `data/events.json` |
| `scripts/sync.py` | Henter Tikkio, Parken, AaFK, Dampsentralen, O'Connor's, Viti, Fabrikken, Liv & Røre, Forum, Vino Bar, Sobra, Devoldfabrikken; slår sammen, bruker overrides, skriver `events.json`, `past.json`, `renamed.json` |
| `scripts/pages.py` | Bygger `_site/`: undersider, sitemap, 404, delingsbilder, ukepost-/panoramabilder |
| `scripts/helgepost.py`, `ukepost.py`, `ikveld.py`, `panorama.py`, `delingsbilde.py`, `kino.py`, `nytt_i_dag.py`, `indexnow.py` | Hjelpeskript |
| `data/manual.json`, `overrides.json`, `julebord.json`, `jul.json` | Håndredigerte data (events.json er generert, aldri rediger) |
| `data/status.json`, `status.html` | Skjult dashboard `status/` |
| `docs/` | Mockuper og forslag (ikke publisert); `docs/HANDOFF-arkiv.md` er full historikk |

## Faste rutiner
- **Ukentlig julesjekk** (Claude-oppgave, mandager 10:23 til 21. des): Bypatrioten, Fjord Norway, Atlanterhavsparken, julegrantenning, kyrkja.alesund.no. Nye desemberkonserter hos Parken er ofte julekonserter uten «jul» i tittelen: legg dem i `data/jul.json` `include`.
- **Vakt** (`trig_01LynTH5ThdCUziUnoPQrC4j`): sjekker at planlagte kjøringer går. Skru av etter jul. Hvis planlagte kjøringer stopper: slå workflowene av og på i Actions, eller merge en liten endring i workflow-filene.
- **Julebord**: sjekk Scandic Parken, MS Bruvik, Hotel 1904 og Quality-hotellene hver uke i november. Neste høst: tøm `julebord.json` og julebord i `manual.json`.
- Etter at kategori eller tittel er feil på nye arrangementer: rett i `overrides.json` (nøkkel = tittel-slug, eller `parken-<nr>`). Dans/ballett/film/foredrag blir ofte gjettet som `konsert`; eieren vil ha `show`.

## Åpne beslutninger og neste steg
1. **Search Console-gjennomgang nr. 3 (1. des.)**: gjort 17. nov (516 klikk, 18 320 visninger, CTR 2,82 %, posisjon ~6; brede søk som «hva skjer i ålesund i dag» er kommet opp av seg selv, avsluttede arrangementssider gir lite, tittel med pris (#155) ikke bevist, titler uendret). Påminnelse 1. des. kl. 09:30 (`send_later`, `trig_0151exxYTsWUhEBRbfprSA2g`; kommer kanskje ikke til en ny økt, så sjekk datoen selv): be om ny zip-eksport og sammenlign med 17. nov, se på julesidene, `julemarked-i-alesund/` (610 visninger, 1,8 % CTR) og scenesidene; ett tiltak om gangen. Detaljer i `docs/HANDOFF-arkiv.md` ("17 Nov 2026: Search Console review no. 2").
2. **Lenker og omtale** (viktigst for trafikk): e-poster til Visit Ålesund, Parken, Løvenvold, Terminalen, Fabrikken; pressetips (julebord-oversikten); eventuell e-post til Bypatrioten om lenkebytte. Claude har tilbudt utkast, ikke skrevet.
3. **Tillatelse**: spør Tikkio før siden promoteres bredt eller `arrangor/` merges/promoteres (vilkårene krever tillatelse for automatisk innhenting og republisering).
4. **Festivalsider 2027** (eierens prioritet 1): tre runder forslag i `docs/festival-forslag*.html`, ingenting valgt. Ålesund Live, WENIFF 4. mars, Warriors of Steel 28. mai, Spirefest 10.–11. sept.
5. **Brosundet ETTER SEKS**: legg inn 2027-datoer når Brosundet publiserer dem.
6. **Musikkquiz på Liv & Røre** er `uncertain` (kl. 18/19): spør Liv & Røre, så kommer quizene med i «Under hundrelappen».
7. «Rigget for fremtiden» (Dampsentralen 17. nov.) står som `konsert`, er trolig fagseminar med rart klokkeslett.
8. Etter ca. 7. nov.: `data/addedat.json` og «Engangsrettelse»-blokken i `sync.py` (~linje 1113) kan fjernes når alle 11 Parken-arrangementene har riktig tid.
9. Bing Webmaster Tools (import fra Search Console), «Gratis og billig»-side, kino-gjennomgang på mobil, AaFK-priser (TicketCo), Aalesunds Museum (Elfsight-widget), iPhone-delingskompass (parkert til nyttår), store mobildesign (parkert til etter jul).
10. Sjekk GoatCounter om noen uker: `nytt/fane`, `lagre/*`, `delt/*`, `sok/*`, `side/*`.

## Gotchas
- Miljøet blokkerer trolig den live siden; test lokalt: `python3 scripts/sync.py`, `python3 scripts/pages.py`, `python3 -m http.server -d _site`. En full `sync.py` kan henge i 10+ minutter: for å teste manuelle arrangementer, legg dem i en midlertidig `events.json`, bygg med `pages.py`, og `git checkout data/events.json` (aldri commit den).
- Boten committer ofte: `git pull` før `git push`. Etter squash-merge: merge `origin/main` inn i branchen (force-push nektes). HANDOFF-endringer når `main` bare via PR.
- `www.`-domener må tillates separat i miljøets nettverksinnstillinger. Sider som blokkerer roboter (Billetto, strawberry.no): ikke omgå, be eieren lime inn teksten.
- Ikke `pkill -f` med mønster som matcher egen shell. Playwright: `npm i playwright-core` og `executablePath: '/opt/pw-browsers/chromium'`.
- Parken kan svare 429: `sync.py` har ventetid og beholder forrige data for feilede sider.
- Tikkios oversikt sier alltid «på lager»; utsolgt-status leses fra hver arrangementsside.
- Instagram-poster: stor tekst (titler ≥ 50 px, mange bilder med få rader). Verifiserte kontoer for tagging: @terminalen_byscene, @lovenvoldtheater, @dampsentralen, @livogrore_moa, @oconnors_alesund, @bryt_tapas, @aalesundsfk, @parken_kulturhus, @sobrascene, @aalesundsfk_kvinner.
