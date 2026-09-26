import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

function ScrollableTable({ children }) {
  const scrollRef = useRef(null)
  const [overflowing, setOverflowing] = useState(false)
  const [moreToTheRight, setMoreToTheRight] = useState(false)

  useEffect(() => {
    const element = scrollRef.current
    if (!element) return undefined
    const update = () => {
      setOverflowing(element.scrollWidth > element.clientWidth + 1)
      setMoreToTheRight(element.scrollWidth - element.clientWidth - element.scrollLeft > 4)
    }
    update()
    const observer = new ResizeObserver(update)
    observer.observe(element)
    element.addEventListener('scroll', update, { passive: true })
    return () => {
      observer.disconnect()
      element.removeEventListener('scroll', update)
    }
  }, [])

  return (
    <div className="my-3">
      <div className="relative">
        <div ref={scrollRef} className="overflow-x-auto rounded-lg border border-line">
          <table className="w-full border-collapse text-left text-xs">{children}</table>
        </div>
        {moreToTheRight && (
          <div className="pointer-events-none absolute inset-y-px right-px w-12 rounded-r-lg bg-gradient-to-l from-surface to-transparent" />
        )}
      </div>
      {overflowing && <p className="mt-1.5 text-[11px] text-subtle">Scroll sideways to see the whole table.</p>}
    </div>
  )
}

const link = (props) => (
  <a {...props} target="_blank" rel="noreferrer" className="text-fg underline decoration-subtle underline-offset-2 hover:decoration-fg" />
)

// Compact styles for chat answers: small headings, tight lists, and tables that scroll
// sideways instead of being clipped by the narrow panel.
const heading = ({ children }) => <h4 className="mb-1.5 mt-5 text-[13px] font-semibold text-fg first:mt-0">{children}</h4>

const chatComponents = {
  a: link,
  h1: heading,
  h2: heading,
  h3: heading,
  h4: heading,
  h5: heading,
  h6: heading,
  p: ({ children }) => <p className="my-2.5 first:mt-0 last:mb-0">{children}</p>,
  ul: ({ children }) => <ul className="my-2.5 list-disc space-y-1.5 pl-5 marker:text-subtle">{children}</ul>,
  ol: ({ children }) => <ol className="my-2.5 list-decimal space-y-1.5 pl-5 marker:text-subtle">{children}</ol>,
  li: ({ children }) => <li className="pl-0.5 [&>ol]:mt-1.5 [&>ul]:mt-1.5">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold text-fg">{children}</strong>,
  hr: () => <hr className="my-4 border-line" />,
  blockquote: ({ children }) => <blockquote className="my-3 border-l-2 border-violet-400/50 pl-3">{children}</blockquote>,
  code: ({ children }) => <code className="rounded bg-raised px-1 py-0.5 text-[0.9em] text-fg">{children}</code>,
  pre: ({ children }) => (
    <pre className="my-3 overflow-x-auto rounded-lg border border-line bg-canvas p-3 text-xs [&_code]:bg-transparent [&_code]:p-0">{children}</pre>
  ),
  table: ({ children }) => <ScrollableTable>{children}</ScrollableTable>,
  thead: ({ children }) => <thead className="bg-raised/70">{children}</thead>,
  th: ({ children }) => <th className="whitespace-nowrap px-3 py-2 align-bottom font-semibold text-fg">{children}</th>,
  td: ({ children }) => <td className="min-w-[7.5rem] border-t border-line px-3 py-2 align-top">{children}</td>,
}

export default function Markdown({ children, variant = 'prose', className = '' }) {
  if (variant === 'chat') {
    return (
      <div className={`text-[13.5px] leading-relaxed text-fg/85 ${className}`}>
        <ReactMarkdown remarkPlugins={[remarkGfm]} components={chatComponents}>
          {children}
        </ReactMarkdown>
      </div>
    )
  }
  return (
    <div className={`prose prose-sm max-w-none prose-p:leading-relaxed prose-headings:font-semibold ${className}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ a: link }}>
        {children}
      </ReactMarkdown>
    </div>
  )
}
