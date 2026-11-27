# 1. søndag i advent: karusell og reel (27.–29. nov 2026)

Alt er laget av `scripts/adventshelg.py` ut fra `data/events.json` og `data/kino.json`.
Karusellen er 9 bilder à 1080 × 1350 (4:5). Reelen er 1080 × 1920, 17 sekunder.

## Når bør det ut?

| Når | Hva |
|---|---|
| **Fredag ca. 12–14** | Karusellen (folk planlegger helga nå) |
| **Fredag ca. 18–19** | Reelen (kveldsscrolling, når folk har bestemt seg for lørdag) |
| **Lørdag ca. 09:30** | Story: karusell-bilde 2 («Perfekt familielørdag») med lenkemerke |
| **Søndag ca. 09:30** | Story: karusell-bilde 3 («Perfekt familiesøndag») med lenkemerke |

Hvert innlegg har en egen lenke slik at du ser i GoatCounter hva som virker:
`https://kaskjerda.no/denne-helgen/?ref=ig-advent` (bio og lenkemerke).

## Karusell: bildetekst

Første linje er det som vises før «mer», så den bærer hele poenget.

```
Første søndag i advent! 🕯️ 19 ting å gjøre i Ålesund denne helga: julemarked, Lysparken, barneshow og adventskonserter.

🎄 LØR 17:00 Lysparken tennes i Spjelkavika. Gratis, fyrverkeri 17:45
🧸 Putti Plutti Pott i Parken: fre, lør og søn
🎅 SØN 12:00 Jul på gården med nissebesøk, Borgund Dyreklubb
🍪 SØN 13:00 Pepperkakeverksted. Gratis
🎬 Julenissens verksted på kino, fra 10:30 lør og søn
🎶 SØN 17:00 Adventskonsert med barnekor. Barn gratis
🛍️ Julemarked: Steinerskolen (lør) og Devoldfabrikken (lør–søn)

📌 Lagre innlegget og send det til den du skal gjøre noe med.
Alle tider, priser og billetter: kaskjerda.no (lenke i bio)

Hva blir din første adventshelg? Skriv 🕯️ i kommentarfeltet hvis dere skal ut!

#ålesund #aalesund #sunnmøre #førsteadvent #helgetips
```

Tre til fem emneknagger holder; Instagram bruker teksten og bildene til å forstå innholdet.
Legg til **Ålesund** som sted.

### Tagging (bruk «Tagg personer» på bildene, maks 20)
- Bilde 5 og 6: @parken_kulturhus
- Bilde 6 og 7: @terminalen_byscene, @lovenvoldtheater
- Bilde 7: @dampsentralen, @livogrore_moa

Vurder å invitere @parken_kulturhus som **medforfatter** (Collab): innlegget vises da på begge profilene og når begge følgerskarene.

### Alternativtekst (Avanserte innstillinger → Skriv alt-tekst)
1. Adventskrans med ett tent lys over Ålesund-silhuett. Tekst: Helga jula starter, første søndag i advent, 19 arrangementer.
2. Tidslinje for en familielørdag: 11:00 julemarked på Steinerskolen, 13:00 Putti Plutti Pott, 17:00 Lysparken tennes.
3. Tidslinje for en familiesøndag: 10:30 Julenissens verksted på kino, 13:00 pepperkakeverksted, 17:00 adventskonsert med barnekor.
4. Lys og marked: Lysparken tennes lørdag 17:00, Designernes julemarked og julemarked på Steinerskolen.
5. Mer for barna: Putti Plutti Pott i Parken, Jul på gården med nissebesøk, barnefilmer på kino.
6. Adventskonserter lørdag og søndag i Ålesund-området. Zimmermann på Løvenvold er utsolgt.
7. Kveldstips for voksne fredag og lørdag: konserter, juleshow og dans.
8. Billetter som går tregt å få tak i: Ålesund symfoniorkester og pepperkakeverksted har få igjen, Zimmermann er utsolgt.
9. Adventskrans og teksten Lagre og send til dem du skal gå med, kaskjerda.no.

## Reel: bildetekst

```
Helga jula starter 🕯️ Lysparken, nissebesøk, pepperkaker, barneshow og adventskonsert. Alt som skjer i Ålesund 27.–29. nov står på kaskjerda.no (lenke i bio). Send til noen du vil gå med 🎄

#ålesund #førsteadvent #sunnmøre
```

### Reel-valg
- **Forsidebilde:** `reel-forside.png`. Teksten ligger midt i bildet, så den vises også i profilrutenettet (4:5-utsnitt).
- **Lyd:** `reel-adventshelg.mp4` har en rolig bjelle-melodi laget for denne reelen, uten opphavsrett. Vil du heller bruke en populær lyd, last opp `reel-adventshelg-stille.mp4` og velg lyd i appen (bedriftskontoer har bare tilgang til det royaltyfrie biblioteket).
- **Prøvereel (Trial Reel):** vurder å dele den først bare til ikke-følgere. Da ser du om den fungerer før den vises til følgerne.
- All tekst står innenfor trygg sone (unntatt øverste og nederste del som appen dekker til med knapper og bildetekst).

## Story-forslag (3 bilder, 15 min arbeid)
1. Bilde 2 eller 3 fra karusellen + **lenkemerke** (`kaskjerda.no/denne-helgen/?ref=ig-advent`).
2. «Hva velger dere?» med avstemning: Lysparken / Pepperkakeverksted / Kino.
3. Lørdag 16:30: «Nå tennes lysene snart» fra Lysparken (egen video, fyrverkeri 17:45).

## Ting som ikke er med, og hvorfor
- **Julegrantenning i Ålesund sentrum** finnes ikke i dataene. Sjekk Bypatrioten/Visit Ålesund og legg den i `data/manual.json` hvis den er denne helga, så kan skriptet kjøres på nytt.
- Julebord er utelatt med vilje (ikke noe for en familiehelg).
- «Jul på gården med nissebesøk» lå som `klubb` fordi stedet heter Borgund Dyreklubb. Rettet til `barn` i `data/overrides.json`.
- Kino viser ikke priser (finnes ikke i dataene).
- «Juleshow på Løvenvold»: oversikten sier at mange forestillinger er utsolgt, men ikke nøyaktig hvilke fredag/lørdag, så bildet sier «sjekk billett».
