import { BriefcaseBusiness, FileText, Network, ScanSearch, TrendingUp } from 'lucide-react'

// Order matches the backend pipeline (app/graph.py).
export const AGENTS = [
  {
    id: 'retriever',
    name: 'Context Retriever',
    role: 'Finds the passages in your document that matter',
    icon: ScanSearch,
    tone: 'bg-cyan-500/15 text-cyan-300 ring-cyan-400/25',
  },
  {
    id: 'analyst',
    name: 'Business Analyst',
    role: 'Maps the business model, tools and bottlenecks',
    icon: BriefcaseBusiness,
    tone: 'bg-violet-500/15 text-violet-300 ring-violet-400/25',
  },
  {
    id: 'architect',
    name: 'Solutions Architect',
    role: 'Designs an automation blueprint for each bottleneck',
    icon: Network,
    tone: 'bg-blue-500/15 text-blue-300 ring-blue-400/25',
  },
  {
    id: 'roi',
    name: 'ROI Analyst',
    role: 'Estimates investment, savings and payback',
    icon: TrendingUp,
    tone: 'bg-emerald-500/15 text-emerald-300 ring-emerald-400/25',
  },
  {
    id: 'report',
    name: 'Report Writer',
    role: 'Writes the executive summary and priorities',
    icon: FileText,
    tone: 'bg-amber-500/15 text-amber-300 ring-amber-400/25',
  },
]

export function stageStatus(job, agentId) {
  if (!job) return 'waiting'
  if (job.completed_stages?.includes(agentId)) return 'done'
  if (job.failed_stage === agentId) return 'failed'
  if (job.status === 'running' && job.stage === agentId) return 'working'
  if (job.status === 'failed') return 'skipped'
  return 'waiting'
}
