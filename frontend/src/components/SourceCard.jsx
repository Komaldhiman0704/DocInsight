import React, { useState } from 'react'
import { FileText, BookOpen, ChevronDown, ChevronUp, Eye, AlertCircle } from 'lucide-react'
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
        <div className="divide-y divide-[var(--border)] animate-expand-smooth">
          {sources.map((s, i) => (
            <div 
              key={i} 
              className="p-3 bg-[var(--bg-primary)] animate-fade-in-delayed"
              style={{ animationDelay: `${i * 0.1}s` }}
            >
              <div className="flex items-center gap-2 mb-1.5">
                <FileText size={12} className="text-[var(--accent)] shrink-0" />
                <span className="font-medium text-[var(--text-primary)] truncate">{s.filename}</span>
                <span className="ml-auto shrink-0 px-1.5 py-0.5 rounded-md bg-[var(--bg-tertiary)] text-[var(--text-muted)] font-mono text-[10px]">
                  p.{s.page}
                </span>
                
                {/* OCR Badge */}
                {s.ocr_used && (
                  <span className="shrink-0 px-1.5 py-0.5 rounded-md bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-[10px] font-medium flex items-center gap-1">
                    <AlertCircle size={9} />
                    OCR
                  </span>
                )}
                
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
              <p className={clsx(
                'text-[var(--text-secondary)] leading-relaxed line-clamp-3',
                'source-highlight rounded px-1 py-0.5'
              )}>
                {s.excerpt}
              </p>
              
              {/* OCR Quality Note */}
              {s.ocr_used && s.quality_score && (
                <p className="mt-1.5 text-[10px] text-blue-600 dark:text-blue-400 flex items-start gap-1">
                  <AlertCircle size={10} className="shrink-0 mt-0.5" />
                  <span>Extracted via OCR - {s.quality_score === 'good' ? 'good quality' : s.quality_score === 'medium' ? 'moderate quality' : 'low quality'}</span>
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
