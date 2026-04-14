import React, { useState } from 'react'
import { FileText, BookOpen, ChevronDown, ChevronUp, Eye } from 'lucide-react'
import clsx from 'clsx'

export default function SourceCard({ sources, onViewPDF }) {
  const [expanded, setExpanded] = useState(false)
  if (!sources || sources.length === 0) return null

  return (
    <div className="mt-3 rounded-lg border border-[var(--border)] overflow-hidden text-xs">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-3 py-2 bg-[var(--bg-secondary)] hover:bg-[var(--bg-tertiary)] transition-colors"
      >
        <div className="flex items-center gap-1.5 text-[var(--text-secondary)] font-medium">
          <BookOpen size={12} />
          <span>{sources.length} source{sources.length > 1 ? 's' : ''} found</span>
        </div>
        {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>

      {/* Source list */}
      {expanded && (
        <div className="divide-y divide-[var(--border)]">
          {sources.map((s, i) => (
            <div key={i} className="p-3 bg-[var(--bg-primary)] animate-fade-in">
              <div className="flex items-center gap-2 mb-1.5">
                <FileText size={12} className="text-[var(--accent)] shrink-0" />
                <span className="font-medium text-[var(--text-primary)] truncate">{s.filename}</span>
                <span className="ml-auto shrink-0 px-1.5 py-0.5 rounded-md bg-[var(--bg-tertiary)] text-[var(--text-muted)] font-mono text-[10px]">
                  p.{s.page}
                </span>
                {onViewPDF && (
                  <button
                    onClick={() => onViewPDF({ id: s.doc_id, filename: s.filename })}
                    className="ml-1 p-1 text-[var(--text-muted)] hover:text-[var(--accent)] transition-colors"
                    title="View PDF"
                  >
                    <Eye size={12} />
                  </button>
                )}
              </div>
              <p className={clsx(
                'text-[var(--text-secondary)] leading-relaxed line-clamp-3',
                'source-highlight rounded px-1 py-0.5'
              )}>
                {s.excerpt}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
