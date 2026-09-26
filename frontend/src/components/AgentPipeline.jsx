import { Check, CircleAlert, LoaderCircle } from 'lucide-react'
import { AGENTS, stageStatus } from '../lib/agents'

const STATUS = {
  waiting: { label: 'Waiting', className: 'text-subtle' },
  working: { label: 'Working', className: 'text-fg' },
  done: { label: 'Done', className: 'text-muted' },
  failed: { label: 'Failed', className: 'text-red-300' },
  skipped: { label: 'Skipped', className: 'text-subtle' },
}

function StatusBadge({ status }) {
  const { label, className } = STATUS[status]
  return (
    <span className={`flex shrink-0 items-center gap-1.5 text-xs font-medium ${className}`}>
      {status === 'working' && <LoaderCircle className="h-3.5 w-3.5 animate-spin text-violet-300" />}
      {status === 'done' && <Check className="h-3.5 w-3.5" />}
      {status === 'failed' && <CircleAlert className="h-3.5 w-3.5 text-red-400" />}
      {(status === 'waiting' || status === 'skipped') && <span className="h-1.5 w-1.5 rounded-full bg-subtle/60" />}
      {label}
    </span>
  )
}

export default function AgentPipeline({ job, showStatus = true }) {
  return (
    <ol className="relative space-y-2">
      {AGENTS.map((agent, index) => {
        const status = stageStatus(job, agent.id)
        const Icon = agent.icon
        const isActive = status === 'working'
        return (
          <li key={agent.id} className="relative">
            {index < AGENTS.length - 1 && (
              <span className="absolute left-[calc(2rem-0.5px)] top-[3.25rem] h-[calc(100%-2.5rem)] w-px bg-line" aria-hidden="true" />
            )}
            <div
              className={`flex items-center gap-4 rounded-xl border px-3 py-3 transition ${
                isActive
                  ? 'border-violet-400/40 bg-violet-500/[0.07] shadow-lg shadow-violet-500/10'
                  : status === 'failed'
                    ? 'border-red-500/30 bg-red-500/[0.06]'
                    : 'border-transparent'
              }`}
            >
              <span className={`relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ring-1 ${agent.tone}`}>
                <Icon className="h-5 w-5" />
                {isActive && <span className="absolute inset-0 animate-ping rounded-xl ring-1 ring-violet-400/40" />}
              </span>
              <div className="min-w-0 flex-1">
                <p className={`text-sm font-semibold ${showStatus && (status === 'waiting' || status === 'skipped') ? 'text-muted' : 'text-fg'}`}>
                  {agent.name}
                </p>
                <p className={`text-xs text-subtle ${showStatus ? 'truncate' : ''}`}>{agent.role}</p>
              </div>
              {showStatus && <StatusBadge status={status} />}
            </div>
          </li>
        )
      })}
    </ol>
  )
}
