import { CircleAlert, RotateCcw } from 'lucide-react'
import AgentPipeline from './AgentPipeline'

export default function FailedView({ job, onReset }) {
  const errors = job.errors?.length ? job.errors : ['The analysis stopped without an error message.']
  return (
    <div className="mx-auto max-w-2xl">
      <div className="card overflow-hidden">
        <div className="border-b border-line p-5 sm:p-6">
          <div className="flex items-start gap-4">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-red-500/15 text-red-300 ring-1 ring-red-400/25">
              <CircleAlert className="h-5 w-5" />
            </span>
            <div>
              <h1 className="text-xl font-semibold text-fg">The analysis couldn't finish</h1>
              <p className="mt-1 text-sm text-muted">{job.filename || 'Pasted text'}</p>
            </div>
          </div>
          <ul className="mt-5 space-y-2">
            {errors.map((error) => (
              <li key={error} className="rounded-lg border border-red-500/25 bg-red-500/[0.07] px-3 py-2 text-sm text-red-100">
                {error}
              </li>
            ))}
          </ul>
        </div>
        <div className="p-3 sm:p-4">
          <AgentPipeline job={job} />
        </div>
      </div>
      <div className="mt-5 flex justify-center">
        <button onClick={onReset} className="btn-primary">
          <RotateCcw className="h-4 w-4" />
          Start a new analysis
        </button>
      </div>
    </div>
  )
}
