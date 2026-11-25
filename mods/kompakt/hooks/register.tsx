import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Routing, Tier, Todo } from '../types'

// Kompakt: oppgavepanel, sparemodus og kostnadsmåler på én statuslinje.
// Panelet åpnes bare når du ber om det (/todo), så det tar ingen plass ellers.

const PANE = 'oppgaver'
const TOOL = 'oppgaver'

const todos = atom({ plugin: 'kompakt', key: 'todos' } as const, [], { shape: 'todos-1' })
const routing = atom({ plugin: 'kompakt', key: 'routing' } as const, {
  isOn: true,
  tier: 'sonnet',
  isManual: false,
  why: 'standard',
})

// ---------- Sparemodus: hvilken modell passer oppgaven ----------

const OPUS =
  /refaktor|refactor|arkitektur|architect|migrer|migrat|sikkerhetshull|security|ytelse|performance|optimaliser|race condition|deadlock|hele (prosjektet|kodebasen|appen)|whole (codebase|project)|planlegg|design(?:e)? (en |et )?ny|vanskelig|komplisert/i
const HAIKU =
  /^(hva|hvor|hvorfor|hvordan|what|where|why|how)\b.{0,80}\?$|hva (er|betyr)|forklar|explain|oversett|translate|gi nytt navn|rename|skrivefeil|typo|stavefeil|vis meg|list(e)? opp|finn filen|hvor er/i
const NAMES: Record<Tier, string> = { haiku: 'haiku', sonnet: 'sonnet', opus: 'opus' }
const RANK: Record<Tier, number> = { haiku: 0, sonnet: 1, opus: 2 }
// Å bytte til en billigere modell midt i en lang samtale gjør at hele konteksten
// må leses inn på nytt uten mellomlager. Under denne grensen lønner byttet seg.
const CHEAP_SWITCH_TOKENS = 30_000

function classify(text: string): { tier: Tier; why: string } {
  const t = text.trim()
  if (OPUS.test(t)) return { tier: 'opus', why: 'stor eller vanskelig oppgave' }
  const words = t.split(/\s+/).filter(Boolean).length
  if (HAIKU.test(t) || (words <= 6 && !/```/.test(t))) return { tier: 'haiku', why: 'kort spørsmål eller liten endring' }
  return { tier: 'sonnet', why: 'vanlig kodeoppgave' }
}

// ---------- Statuslinjen ----------

type Meter = { percent?: number; usd?: number }
let meter: Meter = {}
let warned = 0 // høyeste kontekstvarsel vist: 0, 60 eller 80
const turnsPerTier: Record<Tier, number> = { haiku: 0, sonnet: 0, opus: 0 }

async function refreshStatus($: EngineInterface) {
  const r = await read($, routing)
  const list = await read($, todos)
  const parts: string[] = []

  parts.push(r.isOn ? `${NAMES[r.tier]} ${r.isManual ? '(manuelt)' : '(auto)'}` : 'sparemodus av')

  const p = meter.percent
  if (p !== undefined) {
    const bar = '▓'.repeat(Math.round(p / 20)) + '░'.repeat(5 - Math.round(p / 20))
    parts.push(`kontekst ${bar} ${p} %${p >= 60 ? ' → /compact' : ''}`)
  }
  if (meter.usd !== undefined && meter.usd > 0) parts.push(`≈ $${meter.usd.toFixed(2)}`)
  if (list.length > 0) parts.push(`oppgaver ${list.filter(x => x.isDone).length}/${list.length}`)

  $.ui.status(parts.join(' │ '))
}

async function readUsage($: EngineInterface) {
  try {
    const u = await $.session.usage()
    meter = { percent: u.context.percent, usd: u.cost?.usd }
  } catch {
    // Ingen tall ennå (ny økt): statuslinjen viser bare det den vet.
  }
}

async function remindCompact($: EngineInterface) {
  const p = meter.percent
  if (p === undefined) return
  if (p < 40) {
    warned = 0 // etter /compact: klar til å minne om igjen senere
    return
  }
  if (p >= 80 && warned < 80) {
    warned = 80
    $.ui.toast(
      `Konteksten er ${p} % full. Kjør /compact nå, før neste oppgave. Da blir svarene raskere og billigere, og Claude glemmer ikke viktige detaljer.`,
      { timeoutMs: 12000 },
    )
  } else if (p >= 60 && warned < 60) {
    warned = 60
    $.ui.toast(
      `Konteksten er ${p} % full. Tips: skriv /compact når du er ferdig med denne oppgaven.`,
      { timeoutMs: 8000 },
    )
  }
}

// ---------- Oppgaver ----------

async function saveTodos($: EngineInterface, fn: (list: Todo[]) => Todo[]) {
  await update($, todos, list => fn([...list]))
  await $.store.set('todos', await read($, todos))
  await refreshStatus($)
}

function nextId(list: readonly Todo[]) {
  return list.reduce((max, t) => Math.max(max, t.id), 0) + 1
}

function listText(list: readonly Todo[]) {
  if (list.length === 0) return 'Ingen oppgaver. Legg til med /todo <tekst>.'
  return list.map(t => `${t.isDone ? '[x]' : '[ ]'} ${t.id}. ${t.text}`).join('\n')
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const saved = await $.store.get('todos')
    if (Array.isArray(saved)) await update($, todos, () => saved as Todo[])
    const isOn = await $.store.get('sparemodus')
    if (typeof isOn === 'boolean') await update($, routing, r => ({ ...r, isOn }))

    await $.command.register({
      name: 'todo',
      description: 'Oppgaver: /todo åpner/lukker panelet, /todo <tekst> legger til, /todo ferdig <nr>, /todo fjern <nr>, /todo rydd',
    })
    await $.command.register({
      name: 'sparemodus',
      description: 'Velg modell automatisk: /sparemodus på | av | auto | haiku | sonnet | opus',
    })
    await $.command.register({
      name: 'kostnad',
      description: 'Vis forbruk, kontekst og hvilke modeller sparemodus har brukt',
    })
    await $.tool.register({
      name: TOOL,
      description:
        "The user's personal todo list (shown in a side pane). Use it to add a task the user asks you to remember, or to mark a task done when you have finished it. Actions: list, add (text), done (id).",
      inputSchema: {
        type: 'object',
        properties: {
          action: { type: 'string', enum: ['list', 'add', 'done'] },
          text: { type: 'string' },
          id: { type: 'number' },
        },
        required: ['action'],
      },
      isDeferred: false,
    })

    await readUsage($)
    await refreshStatus($)
    return next(e)
  })

  // ---- Sparemodus: velg modell når du sender en prompt ----
  on('prompt.submit', async ($, e, next) => {
    if (e.command || e.isMeta) return next(e)
    const r = await read($, routing)
    if (!r.isOn) return next(e)

    let text = e.text
    const forced = text.match(/^!(haiku|sonnet|opus|auto)\b\s*/i)
    if (forced) {
      text = text.slice(forced[0].length)
      const word = forced[1]!.toLowerCase()
      if (word === 'auto') {
        await update($, routing, x => ({ ...x, isManual: false }))
      } else {
        await update($, routing, x => ({ ...x, tier: word as Tier, isManual: true, why: 'valgt av deg' }))
      }
    }

    const now = await read($, routing)
    if (!now.isManual) {
      const pick = classify(text)
      const isDown = RANK[pick.tier] < RANK[now.tier]
      const tokens = ((meter.percent ?? 0) / 100) * 200_000
      if (isDown && tokens > CHEAP_SWITCH_TOKENS) {
        // Lang samtale: bli på dagens modell, det er billigere enn å miste mellomlageret.
        await update($, routing, x => ({ ...x, why: 'blir på samme modell (lang samtale)' }))
      } else {
        await update($, routing, x => ({ ...x, tier: pick.tier, why: pick.why }))
      }
    }

    const chosen = await read($, routing)
    turnsPerTier[chosen.tier] += 1
    await refreshStatus($)
    return next(text === e.text ? e : { ...e, text })
  })

  // ---- Sparemodus: send hovedsamtalens forespørsler til valgt modell ----
  on('turn.step', async function* ($, e, next) {
    const r = await read($, routing)
    if (!r.isOn || e.agentId) return yield* next(e)
    return yield* next({ ...e, model: r.tier })
  })

  // ---- Kostnadsmåler: oppdater etter hver tur og minn om /compact ----
  on('turn.complete', async ($, e, next) => {
    const done = await next(e)
    await readUsage($)
    await refreshStatus($)
    await remindCompact($)
    return done
  })

  // ---- Kommandoer ----
  on('command.run', { command: 'todo' }, async ($, e) => {
    const args = e.args.trim()
    const [word = '', ...rest] = args.split(/\s+/)
    const num = Number(rest[0])

    if (args === '') {
      const isUp = (await $.ui.panes()).some(p => p.id === PANE)
      if (isUp) {
        await $.ui.close({ id: PANE })
        return { text: 'Oppgavepanelet er lukket. Fremdriften står fortsatt i statuslinjen.' }
      }
      await $.ui.open({ id: PANE, title: 'Oppgaver' })
      return { text: 'Oppgavepanelet er åpnet. Skriv /todo igjen for å lukke det.' }
    }
    if (/^(ferdig|done)$/i.test(word) && Number.isFinite(num)) {
      await saveTodos($, list => list.map(t => (t.id === num ? { ...t, isDone: !t.isDone, by: 'deg' } : t)))
      return { text: `Oppgave ${num} er oppdatert.` }
    }
    if (/^(fjern|slett|remove)$/i.test(word) && Number.isFinite(num)) {
      await saveTodos($, list => list.filter(t => t.id !== num))
      return { text: `Oppgave ${num} er fjernet.` }
    }
    if (/^(rydd|clear)$/i.test(word)) {
      await saveTodos($, list => list.filter(t => !t.isDone))
      return { text: 'Ferdige oppgaver er fjernet.' }
    }
    if (/^(liste|list|vis)$/i.test(word)) {
      return { text: listText(await read($, todos)) }
    }
    let added = 0
    await saveTodos($, list => {
      added = nextId(list)
      return [...list, { id: added, text: args, isDone: false }]
    })
    return { text: `La til oppgave ${added}: ${args}` }
  })

  on('command.run', { command: 'sparemodus' }, async ($, e) => {
    const arg = e.args.trim().toLowerCase()
    if (arg === 'av' || arg === 'off') {
      await update($, routing, r => ({ ...r, isOn: false }))
      await $.store.set('sparemodus', false)
    } else if (arg === 'haiku' || arg === 'sonnet' || arg === 'opus') {
      await update($, routing, r => ({ ...r, isOn: true, tier: arg as Tier, isManual: true, why: 'valgt av deg' }))
    } else {
      await update($, routing, r => ({ ...r, isOn: true, isManual: false }))
      await $.store.set('sparemodus', true)
    }
    await refreshStatus($)
    const r = await read($, routing)
    return {
      text: !r.isOn
        ? 'Sparemodus er av. Claude Code bruker modellen du har valgt med /model.'
        : r.isManual
          ? `Sparemodus bruker ${r.tier} til du skriver /sparemodus auto.`
          : 'Sparemodus er på: modellen velges automatisk for hver prompt. Start en prompt med !opus, !sonnet eller !haiku for å velge selv.',
    }
  })

  on('command.run', { command: 'kostnad' }, async $ => {
    await readUsage($)
    await refreshStatus($)
    const r = await read($, routing)
    const lines = [
      `Kontekst: ${meter.percent ?? '–'} % full${(meter.percent ?? 0) >= 60 ? '. Kjør /compact snart.' : ''}`,
      `Forbruk i denne økten: ${meter.usd !== undefined ? `≈ $${meter.usd.toFixed(2)} (anslag, ikke faktura; på abonnement er dette inkludert)` : 'ukjent'}`,
      `Sparemodus: ${r.isOn ? `${r.tier}, ${r.why}` : 'av'}`,
      `Prompter per modell: haiku ${turnsPerTier.haiku} · sonnet ${turnsPerTier.sonnet} · opus ${turnsPerTier.opus}`,
    ]
    return { text: lines.join('\n') }
  })

  // ---- Verktøy Claude kan bruke på oppgavelisten ----
  on('tool.run', { tool: `mcp__kompakt__${TOOL}` }, async ($, e) => {
    const input = e as unknown as { action?: string; text?: string; id?: number }
    if (input.action === 'add' && input.text) {
      let added = 0
      await saveTodos($, list => {
        added = nextId(list)
        return [...list, { id: added, text: input.text!, isDone: false }]
      })
      return { result: `Added task ${added}.` }
    }
    if (input.action === 'done' && typeof input.id === 'number') {
      await saveTodos($, list => list.map(t => (t.id === input.id ? { ...t, isDone: true, by: 'claude' } : t)))
      return { result: `Marked task ${input.id} done.` }
    }
    return { result: listText(await read($, todos)) }
  })

  // ---- Panelet ----
  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Button } = $.ui.resolve(e)
    const list = await read($, todos)
    const done = list.filter(t => t.isDone).length

    return (
      <Box flexDirection="column">
        <Text dimColor>
          {done}/{list.length} ferdig
        </Text>
        {list.length === 0 && <Text dimColor>Ingen oppgaver ennå. Skriv /todo og teksten.</Text>}
        {list.map(t => (
          <Box key={`t${t.id}`}>
            <Button
              key={`b${t.id}`}
              label={t.isDone ? '[x]' : '[ ]'}
              onPress={() => saveTodos($, l => l.map(x => (x.id === t.id ? { ...x, isDone: !x.isDone, by: 'deg' } : x)))}
            />
            <Text dimColor={t.isDone} strikethrough={t.isDone}>
              {' '}
              {t.id}. {t.text}
              {t.isDone && t.by === 'claude' ? ' (Claude)' : ''}
            </Text>
          </Box>
        ))}
      </Box>
    )
  })
}
