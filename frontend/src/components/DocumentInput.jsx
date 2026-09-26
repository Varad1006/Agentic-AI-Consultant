import { useState } from 'react'
import { ArrowRight, ClipboardPaste, FileText, FileUp, LoaderCircle, Sparkles, Trash2, Upload } from 'lucide-react'
import { SAMPLE_DOCUMENT } from '../lib/sampleDocument'
import { formatBytes } from '../lib/format'

const ACCEPTED = '.pdf,.docx,.txt,.md,.csv'
const ACCEPTED_EXTENSIONS = ACCEPTED.split(',')
const MIN_CHARS = 50

function Tab({ active, onClick, icon: Icon, children }) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      onClick={onClick}
      className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition sm:flex-none ${
        active ? 'bg-raised text-fg shadow' : 'text-muted hover:text-fg'
      }`}
    >
      <Icon className="h-4 w-4" />
      {children}
    </button>
  )
}

export default function DocumentInput({ onSubmit }) {
  const [mode, setMode] = useState('upload')
  const [file, setFile] = useState(null)
  const [text, setText] = useState('')
  const [dragging, setDragging] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const chooseFile = (candidate) => {
    if (!candidate) return
    const extension = `.${candidate.name.split('.').pop().toLowerCase()}`
    if (!ACCEPTED_EXTENSIONS.includes(extension)) {
      setError(`Unsupported file type. Use PDF, DOCX, TXT, MD or CSV.`)
      return
    }
    setError(null)
    setFile(candidate)
  }

  const loadSample = () => {
    setMode('text')
    setText(SAMPLE_DOCUMENT.text)
    setError(null)
  }

  const canSubmit = mode === 'upload' ? Boolean(file) : text.trim().length >= MIN_CHARS

  const submit = async (event) => {
    event.preventDefault()
    if (!canSubmit || submitting) return
    setSubmitting(true)
    setError(null)
    try {
      await onSubmit(mode === 'upload' ? { file } : { text })
    } catch (err) {
      setError(err.message)
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={submit} className="card p-5 sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div role="tablist" className="flex w-full gap-1 rounded-xl border border-line bg-canvas/60 p-1 sm:w-auto">
          <Tab active={mode === 'upload'} onClick={() => setMode('upload')} icon={Upload}>
            Upload a file
          </Tab>
          <Tab active={mode === 'text'} onClick={() => setMode('text')} icon={ClipboardPaste}>
            Paste text
          </Tab>
        </div>
        <button type="button" onClick={loadSample} className="btn-ghost -mr-2 text-xs">
          <Sparkles className="h-4 w-4 text-violet-300" />
          Try a sample SOP
        </button>
      </div>

      <div className="mt-4">
        {mode === 'upload' ? (
          file ? (
            <div className="flex items-center gap-4 rounded-xl border border-line bg-raised/50 p-4">
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-violet-500/15 text-violet-300 ring-1 ring-violet-400/25">
                <FileText className="h-5 w-5" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-fg">{file.name}</p>
                <p className="text-xs text-subtle">{formatBytes(file.size)} · ready to analyse</p>
              </div>
              <button type="button" onClick={() => setFile(null)} className="btn-ghost" aria-label="Remove file">
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <label
              onDragOver={(event) => {
                event.preventDefault()
                setDragging(true)
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(event) => {
                event.preventDefault()
                setDragging(false)
                chooseFile(event.dataTransfer.files[0])
              }}
              className={`flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border border-dashed px-6 py-10 text-center transition ${
                dragging ? 'border-violet-400 bg-violet-500/10' : 'border-line bg-canvas/40 hover:border-violet-400/50 hover:bg-raised/30'
              }`}
            >
              <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500/20 to-blue-500/20 text-violet-200 ring-1 ring-violet-400/25">
                <FileUp className="h-6 w-6" />
              </span>
              <span>
                <span className="block text-sm font-semibold text-fg">Drop your document here, or click to browse</span>
                <span className="mt-1 block text-xs text-subtle">SOPs, process docs, meeting notes · PDF, DOCX, TXT, MD or CSV up to 10 MB</span>
              </span>
              <input
                type="file"
                accept={ACCEPTED}
                className="sr-only"
                onChange={(event) => {
                  chooseFile(event.target.files[0])
                  event.target.value = ''
                }}
              />
            </label>
          )
        ) : (
          <div className="relative">
            <textarea
              value={text}
              onChange={(event) => setText(event.target.value)}
              placeholder="Paste a description of the business and how its processes work today: who does what, which tools they use, and where time is lost…"
              className="h-56 w-full resize-y rounded-xl border border-line bg-canvas/40 p-4 text-sm leading-relaxed text-fg placeholder:text-subtle focus:border-violet-400/60 focus:outline-none focus:ring-2 focus:ring-violet-400/20"
            />
            <span className="pointer-events-none absolute bottom-3 right-4 text-xs text-subtle">
              {text.length.toLocaleString()} characters
            </span>
          </div>
        )}
      </div>

      {error && (
        <p role="alert" className="mt-3 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
          {error}
        </p>
      )}

      <div className="mt-5 flex flex-col-reverse items-stretch gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs text-subtle">
          {mode === 'text' && text.trim().length > 0 && text.trim().length < MIN_CHARS
            ? `Add at least ${MIN_CHARS} characters so the agents have something to work with.`
            : 'Five agents will analyse it in about 1–3 minutes.'}
        </p>
        <button type="submit" disabled={!canSubmit || submitting} className="btn-primary px-5">
          {submitting ? (
            <>
              <LoaderCircle className="h-4 w-4 animate-spin" />
              Indexing document…
            </>
          ) : (
            <>
              Run analysis
              <ArrowRight className="h-4 w-4" />
            </>
          )}
        </button>
      </div>
    </form>
  )
}
