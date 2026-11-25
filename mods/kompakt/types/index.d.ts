export type Todo = { id: number; text: string; isDone: boolean; by?: 'claude' | 'deg' }
export type Tier = 'haiku' | 'sonnet' | 'opus'
export type Routing = { isOn: boolean; tier: Tier; isManual: boolean; why: string }

declare module 'claude-code' {
  interface PluginState {
    kompakt: {
      todos: Shaped<Todo[]>
      routing: Routing
    }
  }
}
