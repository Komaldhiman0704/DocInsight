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
                    onClick={() => onViewPDF({ 
                      id: s.doc_id, 
                      filename: s.filename,
                      page: s.page  // Pass page number for navigation
                    })}
                    className="ml-1 p-1 text-[var(--text-muted)] hover:text-[var(--accent)] transition-colors"
                    title="View PDF on page"
                  >
                    <Eye size={12} />
                  </button>
                )}
              </div>
              {/* 💡 NEW: Show explanation of why this source matters */}
              {s.explanation && (
                <div className="mt-2 p-2 rounded bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
                  <p className="text-[var(--text-secondary)] text-xs leading-relaxed">
                    <span className="font-semibold text-blue-600 dark:text-blue-400">💡 Why this matters:</span>
                    {' '}
                    {s.explanation}
                  </p>
                </div>
              )}

              <p className={clsx(
                'text-[var(--text-secondary)] leading-relaxed line-clamp-3',
                'source-highlight rounded px-1 py-0.5'
              )}>
                {s.excerpt}
              </p>

              {/* ✅ PHASE 3-4: Display semantic matched text and ranking score */}
              {s.matched_text && (
                <div className="mt-2 pt-2 border-t border-[var(--border)] space-y-1">
                  <div className="text-[10px] text-[var(--text-muted)] italic">
                    <span className="text-[var(--accent)] font-semibold">Key excerpt:</span> "{s.matched_text}"
                  </div>
                  {s.semantic_score !== undefined && (
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 flex-1 rounded-full bg-[var(--bg-tertiary)] overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full transition-all duration-300"
                          style={{ width: `${Math.min(100, (s.semantic_score * 100))}%` }}
                        />
                      </div>
                      <span className="text-[9px] text-[var(--text-muted)] font-mono whitespace-nowrap">
                        {(s.semantic_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
