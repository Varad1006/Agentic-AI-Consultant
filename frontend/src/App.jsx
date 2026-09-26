import { useEffect, useState } from 'react'
import { LoaderCircle, Sparkles, TriangleAlert, WifiOff } from 'lucide-react'
import AgentPipeline from './components/AgentPipeline'
import ChatPanel from './components/ChatPanel'
import DocumentInput from './components/DocumentInput'
import FailedView from './components/FailedView'
import Header from './components/Header'
import ReportView from './components/ReportView'
import RunningView from './components/RunningView'
import { API_URL, api } from './lib/api'

const POLL_INTERVAL_MS = 2000
const RETRY_INTERVAL_MS = 5000

function Notice({ children, tone = 'warning', icon: Icon = TriangleAlert }) {
  const styles =
    tone === 'error'
      ? 'border-red-500/30 bg-red-500/10 text-red-100 [&_svg]:text-red-300'
      : 'border-amber-400/30 bg-amber-400/10 text-amber-100 [&_svg]:text-amber-300'
  return (
    <div role="status" className={`flex gap-3 rounded-xl border p-3.5 text-sm ${styles}`}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
      <div>{children}</div>
    </div>
  )
}

function SetupNotice({ health }) {
  if (!health) return null
  if (health.error) {
    return (
      <Notice tone="error" icon={WifiOff}>
        The API isn't reachable at <code className="text-xs">{API_URL}</code>. Start the backend (see the README), then refresh.
      </Notice>
    )
  }
  const { llm, celery } = health.data
  if (!llm.configured) {
    return (
      <Notice>
        <strong className="font-semibold">GROQ_API_KEY is not set.</strong> Add it to <code className="text-xs">.env</code> and restart the API
        and worker. Keys are free at console.groq.com.
      </Notice>
    )
  }
  if (celery !== 'connected') {
    return <Notice>No Celery worker is running, so analyses will wait in the queue until one starts.</Notice>
  }
  return null
}

function Landing({ health, notice, onSubmit }) {
  const model = health?.data?.llm?.model?.split('/').pop() ?? 'gpt-oss-120b'
  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_22rem] lg:gap-10 xl:grid-cols-[minmax(0,1fr)_24rem]">
      <div className="min-w-0">
        <p className="inline-flex items-center gap-2 rounded-full border border-line bg-surface/70 px-3 py-1 text-xs font-medium text-muted">
          <Sparkles className="h-3.5 w-3.5 text-violet-300" />
          Five specialised agents · {model} on Groq
        </p>
        <h1 className="mt-5 text-4xl font-semibold tracking-tight text-fg sm:text-5xl">
          From documents to <span className="text-gradient">decisions.</span>
        </h1>
        <p className="mt-4 max-w-2xl text-base leading-relaxed text-muted">
          Upload an SOP or process description. A team of AI agents maps your operations, designs an automation
          blueprint, sizes the ROI and writes an executive-ready report you can question.
        </p>
        <div className="mt-6 space-y-3">
          {notice && <Notice>{notice}</Notice>}
          <SetupNotice health={health} />
        </div>
        <div className="mt-6">
          <DocumentInput onSubmit={onSubmit} />
        </div>
      </div>

      <aside className="card h-fit p-5">
        <p className="eyebrow">Your consulting team</p>
        <p className="mt-1 text-sm text-muted">Each agent builds on the previous one's work.</p>
        <div className="mt-4 -mx-2">
          <AgentPipeline showStatus={false} />
        </div>
        <p className="mt-4 border-t border-line pt-4 text-xs leading-relaxed text-subtle">
          Then keep the conversation going: the consultant answers follow-up questions using the report and your document.
        </p>
      </aside>
    </div>
  )
}

export default function App() {
  const [health, setHealth] = useState(null)
  const [jobId, setJobId] = useState(() => new URLSearchParams(window.location.search).get('job'))
  const [job, setJob] = useState(null)
  const [pollError, setPollError] = useState(null)
  const [notice, setNotice] = useState(null)

  useEffect(() => {
    let cancelled = false
    const check = () =>
      api
        .health()
        .then((data) => !cancelled && setHealth({ data }))
        .catch((err) => !cancelled && setHealth({ error: err.message }))
    check()
    const timer = setInterval(check, 30_000)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [])

  // Keep the job in the URL so a refresh (or a shared link) reopens the same report.
  useEffect(() => {
    const url = new URL(window.location.href)
    if (jobId) url.searchParams.set('job', jobId)
    else url.searchParams.delete('job')
    window.history.replaceState(null, '', url)
  }, [jobId])

  useEffect(() => {
    if (!jobId) return undefined
    let cancelled = false
    let timer
    const poll = async () => {
      try {
        const data = await api.getJob(jobId)
        if (cancelled) return
        setJob(data)
        setPollError(null)
        if (data.status === 'queued' || data.status === 'running') timer = setTimeout(poll, POLL_INTERVAL_MS)
      } catch (err) {
        if (cancelled) return
        if (err.status === 404) {
          setNotice("That analysis couldn't be found. Start a new one below.")
          setJobId(null)
          setJob(null)
          return
        }
        setPollError(err.message)
        timer = setTimeout(poll, RETRY_INTERVAL_MS)
      }
    }
    poll()
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [jobId])

  const startJob = async ({ file, text }) => {
    const response = file ? await api.uploadDocument(file) : await api.submitText(text)
    setNotice(null)
    setJob(null)
    setJobId(response.job_id)
    window.scrollTo({ top: 0 })
  }

  const reset = () => {
    setJobId(null)
    setJob(null)
    setPollError(null)
    setNotice(null)
  }

  let content
  if (!jobId) {
    content = <Landing health={health} notice={notice} onSubmit={startJob} />
  } else if (!job) {
    content = (
      <div className="flex items-center justify-center gap-3 py-24 text-sm text-muted">
        <LoaderCircle className="h-5 w-5 animate-spin text-violet-300" />
        Loading analysis…
      </div>
    )
  } else if (job.status === 'queued' || job.status === 'running') {
    content = <RunningView job={job} onReset={reset} />
  } else if (job.status === 'failed') {
    content = <FailedView job={job} onReset={reset} />
  } else {
    content = (
      <div className="grid grid-cols-[minmax(0,1fr)] gap-6 xl:grid-cols-[minmax(0,1fr)_26rem] 2xl:grid-cols-[minmax(0,1fr)_28rem] print:block">
        <ReportView job={job} model={health?.data?.llm?.model} onReset={reset} />
        <aside className="no-print min-w-0 xl:sticky xl:top-24 xl:h-[calc(100vh-7.5rem)]">
          <ChatPanel job={job} onChatUpdate={(chat) => setJob((current) => ({ ...current, chat }))} />
        </aside>
      </div>
    )
  }

  return (
    <div className="min-h-screen print:min-h-0">
      <Header health={health} onHome={reset} />
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-12 print:p-0">
        {pollError && (
          <div className="no-print mb-6">
            <Notice tone="error" icon={WifiOff}>
              Lost connection to the API. Retrying… <span className="text-red-200/70">({pollError})</span>
            </Notice>
          </div>
        )}
        {content}
      </main>
    </div>
  )
}
