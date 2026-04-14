import React from 'react'
import clsx from 'clsx'

export default function ConfidenceIndicator({ confidence, relevance_score, source_count }) {
  if (!confidence) return null

  const confidenceConfig = {
    high: {
      color: 'from-emerald-600 to-emerald-700',
      badge: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
    },
    medium: {
      color: 'from-amber-600 to-amber-700',
      badge: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
    },
    low: {
      color: 'from-slate-500 to-slate-600',
      badge: 'bg-slate-100 text-slate-700 dark:bg-slate-900/40 dark:text-slate-300',
    },
  }

  const config = confidenceConfig[confidence] || confidenceConfig.low
  const confidenceLabel = confidence.charAt(0).toUpperCase() + confidence.slice(1)

  return (
    <div className="flex items-center gap-2 mt-2 text-xs">
      <div className={clsx('px-2 py-1 rounded-md font-medium', config.badge)}>
        {confidenceLabel} • {(relevance_score * 100).toFixed(0)}%
      </div>
      <div className="text-[11px] text-[var(--text-muted)]">
        {source_count} {source_count === 1 ? 'source' : 'sources'}
      </div>
    </div>
  )
}
