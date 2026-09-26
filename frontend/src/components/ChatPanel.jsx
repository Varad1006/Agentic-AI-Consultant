import { forwardRef, useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Bot, Check, Copy, Maximize2, Minimize2, RotateCcw, Send } from 'lucide-react'
import Markdown from './Markdown'
import { api } from '../lib/api'

const SUGGESTIONS = [
  'Which initiative should we start with, and why?',
  'Walk me through how the ROI was estimated.',
  'What are the biggest implementation risks?',
  'Draft a 90-day rollout plan.',
]

function ConsultantLabel({ children }) {
  return (
    <div className="mb-2 flex items-center gap-2">
      <span className="flex h-6 w-6 items-center justify-center rounded-md bg-violet-500/15 text-violet-300 ring-1 ring-violet-400/25">
        <Bot className="h-3.5 w-3.5" />
      </span>
      <span className="text-xs font-semibold text-fg">Consultant</span>
      {children}
    </div>
  )
}

const UserMessage = forwardRef(function UserMessage({ children }, ref) {
  return (
    <div ref={ref} className="flex justify-end">
      <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-gradient-to-br from-violet-500 to-blue-600 px-4 py-2.5 text-sm text-white shadow-lg shadow-violet-500/10">
        {children}
      </div>
    </div>
  )
})

function AssistantMessage({ content }) {
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // Clipboard access can be blocked; nothing useful to do.
    }
  }

  return (
    <div className="group">
      <ConsultantLabel>
        <button
          onClick={copy}
          className="ml-auto flex items-center gap-1 rounded-md px-1.5 py-1 text-[11px] text-subtle transition hover:bg-raised hover:text-fg focus:opacity-100 sm:opacity-0 sm:group-hover:opacity-100"
          aria-label="Copy answer"
        >
          {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </ConsultantLabel>
      <Markdown variant="chat">{content}</Markdown>
    </div>
  )
}

function Thinking() {
  return (
    <div>
      <ConsultantLabel />
      <div className="flex items-center gap-2 text-xs text-subtle" aria-label="Consultant is thinking">
        <span className="flex gap-1">
          {[0, 150, 300].map((delay) => (
            <span key={delay} className="h-1.5 w-1.5 animate-bounce rounded-full bg-subtle" style={{ animationDelay: `${delay}ms` }} />
          ))}
        </span>
        Thinking it through…
      </div>
    </div>
  )
}

export default function ChatPanel({ job, onChatUpdate }) {
  const [draft, setDraft] = useState('')
  const [pending, setPending] = useState(null)
  const [error, setError] = useState(null)
  const [expanded, setExpanded] = useState(false)
  const scrollRef = useRef(null)
  const lastQuestionRef = useRef(null)
  const messages = job.chat ?? []
  const lastQuestionIndex = messages.map((message) => message.role).lastIndexOf('user')

  // While waiting, keep the bottom in view; once an answer arrives, show it from the question
  // down, so long answers are read from the top.
  useEffect(() => {
    const container = scrollRef.current
    if (container && (pending || error)) container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' })
  }, [pending, error])

  useEffect(() => {
    const container = scrollRef.current
    const question = lastQuestionRef.current
    if (container && question) container.scrollTo({ top: question.offsetTop - 16, behavior: 'smooth' })
  }, [messages.length, expanded])

  useEffect(() => {
    if (!expanded) return undefined
    const closeOnEscape = (event) => event.key === 'Escape' && setExpanded(false)
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', closeOnEscape)
    return () => {
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', closeOnEscape)
    }
  }, [expanded])

  const send = async (question) => {
    const text = question.trim()
    if (!text || pending) return
    setDraft('')
    setError(null)
    setPending(text)
    try {
      const data = await api.ask(job.job_id, text)
      onChatUpdate(data.chat)
    } catch (err) {
      setError({ message: err.message, question: text })
    } finally {
      setPending(null)
    }
  }

  const column = expanded ? 'mx-auto w-full max-w-3xl' : ''

  const panel = (
    <div
      role={expanded ? 'dialog' : undefined}
      aria-modal={expanded || undefined}
      aria-label="Consultant chat"
      className={
        expanded
          ? 'card no-print fixed inset-3 z-50 flex flex-col overflow-hidden bg-surface sm:inset-y-4 sm:left-auto sm:right-4 sm:w-[min(56rem,calc(100vw-2rem))]'
          : 'card flex h-[36rem] flex-col overflow-hidden xl:h-full'
      }
    >
      <div className="flex items-center gap-3 border-b border-line px-5 py-4">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-blue-500 text-white">
          <Bot className="h-5 w-5" />
        </span>
        <div className="min-w-0 flex-1">
          <h2 className="text-sm font-semibold text-fg">Ask your consultant</h2>
          <p className="truncate text-xs text-subtle">Grounded in this report and your document</p>
        </div>
        <button
          onClick={() => setExpanded((value) => !value)}
          className="btn-ghost h-8 w-8 shrink-0 p-0"
          aria-label={expanded ? 'Collapse chat' : 'Expand chat'}
          title={expanded ? 'Collapse (Esc)' : 'Expand'}
        >
          {expanded ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
        </button>
      </div>

      <div ref={scrollRef} className="relative flex-1 overflow-y-auto px-4 py-5 sm:px-5">
        <div className={`space-y-7 ${column}`}>
          {messages.length === 0 && !pending && (
            <div>
              <p className="text-sm text-muted">Dig deeper into the findings. The consultant remembers this conversation.</p>
              <div className="mt-4 space-y-2">
                {SUGGESTIONS.map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => send(suggestion)}
                    className="block w-full rounded-xl border border-line bg-raised/30 px-3.5 py-2.5 text-left text-sm text-fg transition hover:border-violet-400/40 hover:bg-violet-500/[0.07]"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message, index) =>
            message.role === 'user' ? (
              <UserMessage key={index} ref={index === lastQuestionIndex ? lastQuestionRef : undefined}>
                {message.content}
              </UserMessage>
            ) : (
              <AssistantMessage key={index} content={message.content} />
            ),
          )}

          {pending && (
            <>
              <UserMessage>{pending}</UserMessage>
              <Thinking />
            </>
          )}

          {error && (
            <div role="alert" className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-100">
              <p>{error.message}</p>
              <button onClick={() => send(error.question)} className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold text-red-200 hover:text-white">
                <RotateCcw className="h-3.5 w-3.5" />
                Try again
              </button>
            </div>
          )}
        </div>
      </div>

      <form
        onSubmit={(event) => {
          event.preventDefault()
          send(draft)
        }}
        className="border-t border-line p-3"
      >
        <div className={column}>
          <div className="flex items-end gap-2 rounded-xl border border-line bg-canvas/50 p-1.5 focus-within:border-violet-400/60 focus-within:ring-2 focus-within:ring-violet-400/20">
            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault()
                  send(draft)
                }
              }}
              rows={Math.min(5, Math.max(1, draft.split('\n').length))}
              placeholder="Ask a follow-up question…"
              className="max-h-32 flex-1 resize-none bg-transparent px-2.5 py-2 text-sm text-fg placeholder:text-subtle focus:outline-none"
            />
            <button type="submit" disabled={!draft.trim() || Boolean(pending)} className="btn-primary h-9 w-9 shrink-0 p-0" aria-label="Send">
              <Send className="h-4 w-4" />
            </button>
          </div>
          <p className="mt-1.5 px-1 text-[11px] text-subtle">Enter to send · Shift+Enter for a new line</p>
        </div>
      </form>
    </div>
  )

  if (!expanded) return panel

  // Rendered on <body> so the drawer sits above the sticky page header.
  return createPortal(
    <>
      <div className="no-print fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" onClick={() => setExpanded(false)} aria-hidden="true" />
      {panel}
    </>,
    document.body,
  )
}
