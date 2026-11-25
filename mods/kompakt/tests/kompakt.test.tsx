import { expect, mock, test } from 'claude-code/testing'

const PANE = {
  plugin: 'kompakt',
  component: 'Pane',
  requestId: 'oppgaver',
  props: {
    title: 'Oppgaver',
    isFocused: false,
    bodyColumns: 30,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 20 },
    view: {},
  },
} as const

function engine(on: any, percent?: number) {
  mock.store(on)
  on('command.register', (_: unknown, e: any) => ({ value: { command: e.name } }))
  on('tool.register', () => ({ value: {} }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.panes', () => ({ value: [] }))
  on('session.start', (_: unknown, e: any) => ({ cwd: e.cwd }))
  on('session.usage', () => ({
    value: { startedAt: 0, context: { window: 200000, percent }, rateLimits: [], cost: { usd: 0.42 } },
  }))
}

test('/todo legger til en oppgave og panelet viser den', async ($, on) => {
  engine(on)
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  const r = await $.command.run({ command: 'todo', args: 'kjøp domene' } as any)
  expect(r.text).toBe('La til oppgave 1: kjøp domene')

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect((await ui.find({ type: 'Text', text: /kjøp domene/ }))).toBeDefined()
  await ui.press({ key: 'b1' })
  expect((await ui.find({ type: 'Text', text: /1\/1 ferdig/ }))).toBeDefined()
  await ui.unmount()
})

test('!opus i starten velger modell og fjernes fra teksten', async ($, on) => {
  engine(on, 65)
  let sent = ''
  on('prompt.submit', (_: unknown, e: any) => {
    sent = e.text
    return { text: e.text }
  })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.prompt.submit({ text: '!opus skriv om README' } as any)
  expect(sent).toBe('skriv om README')
  const k = await $.command.run({ command: 'kostnad', args: '' } as any)
  expect(k.text).toMatch(/Sparemodus: opus/)
  expect(k.text).toMatch(/Kjør \/compact snart/)
})

test('kort spørsmål går til haiku', async ($, on) => {
  engine(on)
  on('prompt.submit', (_: unknown, e: any) => ({ text: e.text }))
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.prompt.submit({ text: 'hva betyr denne feilmeldingen?' } as any)
  const k = await $.command.run({ command: 'kostnad', args: '' } as any)
  expect(k.text).toMatch(/Sparemodus: haiku/)
})

test('minner om /compact én gang når konteksten passerer 60 %', async ($, on) => {
  engine(on, 64)
  const toasts: string[] = []
  on('ui.toast', (_: unknown, e: any) => {
    toasts.push(e.text)
    return { value: undefined }
  })
  on('ui.status', () => ({ value: undefined }))
  on('turn.complete', () => ({ text: 'ok' }))
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.turn.complete({ turnId: 't1', answer: 'ok', reason: 'end_turn' } as any)
  await $.turn.complete({ turnId: 't2', answer: 'ok', reason: 'end_turn' } as any)
  expect(toasts.length).toBe(1)
  expect(toasts[0]).toMatch(/\/compact/)
})
