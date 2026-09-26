import { useState } from 'react'
import {
  ArrowLeft,
  CalendarClock,
  Check,
  Download,
  Hourglass,
  LoaderCircle,
  Percent,
  PiggyBank,
  Printer,
  Wallet,
  Wrench,
} from 'lucide-react'
import Markdown from './Markdown'
import { api } from '../lib/api'
import { formatCurrency, formatDateTime, formatNumber } from '../lib/format'

function Section({ eyebrow, title, description, children }) {
  return (
    <section className="card p-5 sm:p-6">
      <header className="avoid-break mb-5">
        <p className="eyebrow">{eyebrow}</p>
        <h2 className="mt-1 text-lg font-semibold text-fg">{title}</h2>
        {description && <p className="mt-1 text-sm text-muted">{description}</p>}
      </header>
      {children}
    </section>
  )
}

function StatTile({ icon: Icon, label, value, detail }) {
  return (
    <div className="card avoid-break p-4">
      <div className="flex items-center gap-2 text-xs font-medium text-muted">
        <Icon className="h-4 w-4 text-subtle" />
        {label}
      </div>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-fg">{value}</p>
      <p className="mt-0.5 text-xs text-subtle">{detail}</p>
    </div>
  )
}

function BottleneckChart({ bottlenecks }) {
  const sorted = [...bottlenecks].sort((a, b) => b.current_time_spent_hours - a.current_time_spent_hours)
  const max = Math.max(...sorted.map((b) => b.current_time_spent_hours), 1)
  return (
    <ul className="space-y-5">
      {sorted.map((bottleneck) => {
        const hours = bottleneck.current_time_spent_hours
        return (
          <li key={bottleneck.process_name} className="avoid-break">
            <p className="text-sm font-semibold text-fg">{bottleneck.process_name}</p>
            <div className="group relative mt-2 flex items-center gap-3 py-1" tabIndex={0}>
              {/* Bars grow from a shared baseline; the value sits at the tip in text colour. */}
              <div
                className="h-2.5 rounded-r bg-violet-500"
                style={{ width: `${Math.max((hours / max) * 82, 1.5)}%` }}
              />
              <span className="shrink-0 text-sm font-medium tabular-nums text-fg">
                {formatNumber(hours)} h<span className="text-subtle">/week</span>
              </span>
              <span className="no-print pointer-events-none absolute -top-9 left-0 z-10 hidden whitespace-nowrap rounded-lg border border-line bg-raised px-2.5 py-1.5 text-xs text-fg shadow-lg group-hover:block group-focus:block">
                {bottleneck.process_name}: {formatNumber(hours)} h/week ≈ {formatNumber(hours * 52, 0)} h/year
              </span>
            </div>
            <p className="mt-1.5 text-sm leading-relaxed text-muted">{bottleneck.pain_point_description}</p>
          </li>
        )
      })}
    </ul>
  )
}

function SolutionCard({ solution }) {
  return (
    <article className="avoid-break flex flex-col rounded-xl border border-line bg-raised/40 p-5">
      <p className="eyebrow">Targets</p>
      <h3 className="mt-1 font-semibold text-fg">{solution.target_bottleneck}</h3>
      <p className="mt-3 flex items-start gap-2 rounded-lg bg-blue-500/10 px-3 py-2 text-sm text-fg ring-1 ring-blue-400/20">
        <Wrench className="mt-0.5 h-4 w-4 shrink-0 text-blue-300" />
        {solution.recommended_technology}
      </p>
      <ol className="mt-4 space-y-2.5">
        {solution.implementation_steps.map((step, index) => (
          <li key={index} className="flex gap-3 text-sm leading-relaxed text-muted">
            <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-canvas text-[11px] font-semibold text-fg ring-1 ring-line">
              {index + 1}
            </span>
            <span>{step}</span>
          </li>
        ))}
      </ol>
    </article>
  )
}

export default function ReportView({ job, model, onReset }) {
  const { analysis, architecture, roi, report } = job.result
  const [downloading, setDownloading] = useState(false)
  const totalHours = analysis.identified_bottlenecks.reduce((sum, b) => sum + b.current_time_spent_hours, 0)

  const downloadMarkdown = async () => {
    setDownloading(true)
    try {
      const { content } = await api.getReportMarkdown(job.job_id)
      const url = URL.createObjectURL(new Blob([content], { type: 'text/markdown' }))
      const link = Object.assign(document.createElement('a'), {
        href: url,
        download: `consulting-report-${job.job_id.slice(0, 8)}.md`,
      })
      link.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      alert(`Could not download the report: ${err.message}`)
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="min-w-0 space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="min-w-0">
          <p className="eyebrow">Executive consulting report</p>
          <h1 className="mt-2 truncate text-2xl font-semibold tracking-tight text-fg sm:text-3xl">
            {job.filename || 'Pasted document'}
          </h1>
          <p className="mt-1 text-sm text-subtle">
            Generated {formatDateTime(job.created_at)} · Ref {job.job_id.slice(0, 8)}
          </p>
        </div>
        <div className="no-print flex shrink-0 flex-wrap gap-2">
          <button onClick={onReset} className="btn-ghost">
            <ArrowLeft className="h-4 w-4" />
            New analysis
          </button>
          <button onClick={downloadMarkdown} disabled={downloading} className="btn-secondary">
            {downloading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
            Markdown
          </button>
          <button onClick={() => window.print()} className="btn-secondary">
            <Printer className="h-4 w-4" />
            Export PDF
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5 print:grid-cols-5">
        <StatTile icon={Wallet} label="Investment" value={formatCurrency(roi.estimated_development_cost_usd)} detail="One-off build cost" />
        <StatTile icon={PiggyBank} label="Annual savings" value={formatCurrency(roi.estimated_annual_monetary_savings_usd)} detail="Recurring, per year" />
        <StatTile
          icon={CalendarClock}
          label="Payback"
          value={roi.payback_period_months == null ? '—' : `${formatNumber(roi.payback_period_months)} mo`}
          detail="To break even"
        />
        <StatTile
          icon={Percent}
          label="3-year ROI"
          value={roi.roi_percentage == null ? '—' : `${formatNumber(roi.roi_percentage, 0)}%`}
          detail="Net return"
        />
        <StatTile icon={Hourglass} label="Hours freed" value={formatNumber(roi.annual_hours_saved, 0)} detail="Per year" />
      </div>

      <section className="card relative overflow-hidden p-5 sm:p-6">
        <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-violet-500 via-indigo-500 to-blue-500" />
        <p className="eyebrow">Executive summary</p>
        <Markdown className="mt-3 text-[15px]">{report.executive_summary.replace(/\\n/g, '\n')}</Markdown>
        <h3 className="mt-6 text-sm font-semibold text-fg">Priority actions</h3>
        <ol className="mt-3 space-y-2.5">
          {report.priority_actions.map((action, index) => (
            <li key={index} className="avoid-break flex gap-3 rounded-xl border border-line bg-raised/40 p-3 text-sm leading-relaxed text-fg">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500 to-blue-500 text-xs font-semibold text-white">
                {index + 1}
              </span>
              <span>{action}</span>
            </li>
          ))}
        </ol>
      </section>

      <Section
        eyebrow="Current state"
        title="Where time is lost"
        description={`${formatNumber(totalHours)} hours a week across ${analysis.identified_bottlenecks.length} processes (≈ ${formatNumber(totalHours * 52, 0)} hours a year).`}
      >
        <p className="text-sm leading-relaxed text-muted">{analysis.core_business_model}</p>
        {analysis.current_tech_stack.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {analysis.current_tech_stack.map((tool) => (
              <span key={tool} className="rounded-full border border-line bg-raised/50 px-3 py-1 text-xs text-fg">
                {tool}
              </span>
            ))}
          </div>
        )}
        <div className="mt-6 border-t border-line pt-6">
          <p className="mb-4 text-xs font-medium text-subtle">Hours spent per week, by process</p>
          <BottleneckChart bottlenecks={analysis.identified_bottlenecks} />
        </div>
      </Section>

      <Section eyebrow="Automation blueprint" title="What to build" description={architecture.overall_strategy}>
        <div className="grid gap-4 lg:grid-cols-2 print:grid-cols-2">
          {architecture.proposed_solutions.map((solution, index) => (
            <SolutionCard key={index} solution={solution} />
          ))}
        </div>
        {architecture.infrastructure_requirements.length > 0 && (
          <div className="mt-6 border-t border-line pt-5">
            <h3 className="text-sm font-semibold text-fg">Infrastructure requirements</h3>
            <ul className="mt-3 grid gap-2 sm:grid-cols-2">
              {architecture.infrastructure_requirements.map((item) => (
                <li key={item} className="flex gap-2 text-sm text-muted">
                  <Check className="mt-0.5 h-4 w-4 shrink-0 text-subtle" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}
      </Section>

      <Section
        eyebrow="Financial case"
        title="How the numbers were estimated"
        description="Payback and ROI are calculated from the cost and savings estimates, so they always agree. Treat all figures as directional."
      >
        <ul className="space-y-2">
          {roi.key_assumptions.map((assumption) => (
            <li key={assumption} className="flex gap-2 text-sm leading-relaxed text-muted">
              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-subtle" />
              {assumption}
            </li>
          ))}
        </ul>
      </Section>

      <p className="pb-2 text-center text-xs text-subtle">
        Prepared by five AI agents{model ? ` using ${model} on Groq` : ''}. Review before acting on it.
      </p>
    </div>
  )
}
