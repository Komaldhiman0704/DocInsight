import React from 'react'
import { AlertCircle, CheckCircle2 } from 'lucide-react'
import clsx from 'clsx'

export default function ConfidenceIndicator({ confidence, relevance_score, source_count, ocr_sources }) {
  if (!confidence) return null

  const confidenceConfig = {
    high: {
      color: 'from-emerald-600 to-emerald-700',
      badge: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
      icon: CheckCircle2,
    },
    medium: {
      color: 'from-amber-600 to-amber-700',
      badge: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
      icon: AlertCircle,
    },
    low: {
      color: 'from-slate-500 to-slate-600',
      badge: 'bg-slate-100 text-slate-700 dark:bg-slate-900/40 dark:text-slate-300',
      icon: AlertCircle,
    },
  }

  const config = confidenceConfig[confidence] || confidenceConfig.low
  const Icon = config.icon
  const confidenceLabel = confidence.charAt(0).toUpperCase() + confidence.slice(1)

  return (
    <div className="flex flex-col gap-1.5 mt-2 text-xs">
      <div className="flex items-center gap-2">
        <div className={clsx('flex items-center gap-1 px-2 py-1 rounded-md font-medium', config.badge)}>
          <Icon size={12} />
          <span>{confidenceLabel} • {(relevance_score * 100).toFixed(0)}%</span>
        </div>
        <div className="text-[11px] text-[var(--text-muted)]">
          {source_count} {source_count === 1 ? 'source' : 'sources'}
        </div>
      </div>
      
      {/* OCR Warning */}
      {ocr_sources && (
        <div className="flex items-start gap-1.5 px-2 py-1 rounded bg-blue-50 dark:bg-blue-950/30 text-blue-700 dark:text-blue-300 text-[10px]">
          <AlertCircle size={11} className="shrink-0 mt-0.5" />
          <span>
            Some sources use OCR extraction - accuracy may vary on handwritten or image-based PDFs
          </span>
        </div>
      )}
    </div>
  )
}
