import React, { useState } from 'react'
import { Copy, CheckCircle, Sparkles } from 'lucide-react'
import toast from 'react-hot-toast'
import clsx from 'clsx'

export default function DocumentSummaryCard({ summary, filename, isGenerating = false }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(summary || '')
    setCopied(true)
    toast.success('Summary copied to clipboard')
    setTimeout(() => setCopied(false), 2000)
  }

  // Shimmer loading state (3 gray lines)
  if (isGenerating) {
    return (
      <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] p-4 space-y-2.5">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles size={14} className="text-amber-500 animate-pulse" />
          <p className="text-xs font-medium text-[var(--text-muted)]">Generating summary…</p>
        </div>
        {[1, 2, 3].map(i => (
          <div key={i} className="h-3 bg-[var(--bg-tertiary)] rounded shimmer" style={{ width: 80 + i * 5 + '%' }} />
        ))}
      </div>
    )
  }

  // No summary yet
  if (!summary) {
    return null
  }

  return (
    <div
      onClick={handleCopy}
      className={clsx(
        'rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] p-4',
        'cursor-pointer transition-all duration-200',
        'hover:border-[var(--accent)] hover:shadow-md hover:shadow-blue-100 dark:hover:shadow-blue-950/30',
        'group'
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-2.5">
        <div className="flex items-center gap-2">
          <Sparkles size={14} className="text-amber-500 shrink-0" />
          <p className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wide">
            AI Summary
          </p>
        </div>
        <button
          onClick={e => {
            e.stopPropagation()
            handleCopy()
          }}
          className={clsx(
            'p-1 rounded transition-all duration-200 shrink-0',
            copied
              ? 'text-green-500 bg-green-500/10'
              : 'text-[var(--text-muted)] opacity-0 group-hover:opacity-100 hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]'
          )}
          title={copied ? 'Copied!' : 'Copy summary'}
        >
          {copied ? <CheckCircle size={14} /> : <Copy size={14} />}
        </button>
      </div>

      {/* Summary text */}
      <p className="text-sm leading-relaxed text-[var(--text-primary)]">
        {summary}
      </p>

      {/* Hint */}
      <p className="text-[10px] text-[var(--text-muted)] mt-2.5">
        Click to copy
      </p>
    </div>
  )
}
