# kompakt

Tre verktøy i én mod som bare tar én linje, laget for små skjermer:

- **Oppgavepanel**: `/todo` åpner og lukker panelet. `/todo <tekst>` legger til en oppgave, `/todo ferdig <nr>` krysser av, `/todo fjern <nr>` fjerner, `/todo rydd` fjerner ferdige oppgaver. Claude kan også legge til og krysse av oppgaver. Listen huskes mellom økter.
- **Sparemodus**: velger Haiku, Sonnet eller Opus for hver prompt ut fra hva du ber om. Start en prompt med `!opus`, `!sonnet` eller `!haiku` for å velge selv, `!auto` for å slå tilbake på automatikk. `/sparemodus av` slår funksjonen av.
- **Kostnadsmåler**: statuslinjen viser kontekst og forbruk (anslag). Ved 60 % og 80 % får du et varsel om å kjøre `/compact`. `/kostnad` viser detaljer.
