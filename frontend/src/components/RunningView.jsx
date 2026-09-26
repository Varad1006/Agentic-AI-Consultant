import { useEffect, useState } from 'react'
import { Clock, FileText, TriangleAlert } from 'lucide-react'
import AgentPipeline from './AgentPipeline'
import { AGENTS } from '../lib/agents'
import { formatDuration } from '../lib/format'

const WORKER_WARNING_AFTER_SECONDS = 15

function useElapsedSeconds(since) {
  const [now, setNow] = useState(Date.now())
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(timer)
  }, [])
  return since ? (now - new Date(since).getTime()) / 1000 : 0
}

export default function RunningView({ job, onReset }) {
  const elapsed = useElapsedSeconds(job?.created_at)
  const completed = job?.completed_stages?.length ?? 0
  const progress = Math.round((completed / AGENTS.length) * 100)
  const currentAgent = AGENTS.find((agent) => agent.id === job?.stage)
  const waitingForWorker = job?.status === 'queued' && elapsed > WORKER_WARNING_AFTER_SECONDS

  return (
    <div className="mx-auto max-w-2xl">
      <div className="card overflow-hidden">
        <div className="border-b border-line p-5 sm:p-6">
          <p className="eyebrow">Analysis in progress</p>
          <h1 className="mt-2 text-xl font-semibold text-fg sm:text-2xl">
            {job?.status === 'running' && currentAgent ? `${currentAgent.name} is working…` : 'Waiting for the agents…'}
          </h1>
          <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1 text-sm text-muted">
            <span className="flex min-w-0 items-center gap-1.5">
              <FileText className="h-4 w-4 shrink-0 text-subtle" />
              <span className="truncate">{job?.filename || 'Pasted text'}</span>
              {job && <span className="text-subtle">· {job.characters.toLocaleString()} characters</span>}
            </span>
            <span className="flex items-center gap-1.5 tabular-nums">
              <Clock className="h-4 w-4 text-subtle" />
              {formatDuration(elapsed)}
            </span>
          </div>
          <div
            className="mt-5 h-1.5 overflow-hidden rounded-full bg-raised"
            role="progressbar"
            aria-valuenow={progress}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label="Pipeline progress"
          >
            <div
              className="h-full rounded-full bg-gradient-to-r from-violet-500 to-blue-500 transition-all duration-700"
              style={{ width: `${Math.max(progress, 4)}%` }}
            />
          </div>
        </div>

        <div className="p-3 sm:p-4">
          <AgentPipeline job={job} />
        </div>

        {waitingForWorker && (
          <div className="mx-5 mb-5 flex gap-3 rounded-xl border border-amber-400/30 bg-amber-400/10 p-3 text-sm text-amber-100 sm:mx-6">
            <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" />
            <p>
              No worker has picked this job up yet. Make sure the Celery worker is running
              (<code className="text-xs">celery -A app.celery_worker.celery_app worker</code>).
            </p>
          </div>
        )}
        {job?.truncated && (
          <p className="mx-5 mb-5 text-xs text-subtle sm:mx-6">
            The document was longer than the analysis limit, so only the first part is being used.
          </p>
        )}
      </div>

      <div className="mt-4 flex flex-col items-center gap-2 text-center text-xs text-subtle">
        <p>You can leave this page open. On Groq's free tier the agents may pause briefly for rate limits.</p>
        <button onClick={onReset} className="btn-ghost text-xs">
          Start a different analysis
        </button>
      </div>
    </div>
  )
}
