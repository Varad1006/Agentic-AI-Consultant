import Logo from './Logo'

function healthState(health) {
  if (!health) return { dot: 'bg-subtle animate-pulse', label: 'Checking API…' }
  if (health.error) return { dot: 'bg-red-500', label: 'API offline', title: health.error }
  const { llm, celery } = health.data
  if (!llm.configured) return { dot: 'bg-amber-400', label: 'Groq key missing' }
  if (celery !== 'connected') return { dot: 'bg-amber-400', label: 'No worker running' }
  return { dot: 'bg-emerald-400', label: `${llm.model.split('/').pop()} · Groq` }
}

export default function Header({ health, onHome }) {
  const state = healthState(health)
  return (
    <header className="no-print sticky top-0 z-20 border-b border-line/70 bg-canvas/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6">
        <button onClick={onHome} className="flex items-center gap-3 rounded-lg text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400/60">
          <Logo />
          <span className="leading-tight">
            <span className="block text-sm font-semibold text-fg sm:text-base">Autonomous AI Consultant</span>
            <span className="hidden text-xs text-subtle sm:block">Multi-agent business process analysis</span>
          </span>
        </button>
        <div
          className="flex shrink-0 items-center gap-2 whitespace-nowrap rounded-full border border-line bg-surface/80 px-3 py-1.5 text-xs font-medium text-muted"
          title={state.title}
        >
          <span className={`h-2 w-2 rounded-full ${state.dot}`} />
          {state.label}
        </div>
      </div>
    </header>
  )
}
