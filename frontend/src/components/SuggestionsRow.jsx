import React, { useState } from 'react'
import { ChevronDown, Sparkles, ArrowRight } from 'lucide-react'
import clsx from 'clsx'

export default function SuggestionsRow({ suggestions, onSuggestionClick, disabled = false }) {
  const [expanded, setExpanded] = useState(false)
  const [hoveredIdx, setHoveredIdx] = useState(null)
  
  if (!suggestions || suggestions.length === 0) return null

  return (
    <div className="w-full mt-4">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        disabled={disabled}
        className={clsx(
          'group flex items-center gap-2.5 text-sm font-medium',
          'text-[var(--text-secondary)] hover:text-[var(--text-primary)]',
          'transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed',
          'hover:gap-3'
        )}
      >
        <div className={clsx(
          'flex items-center justify-center w-5 h-5 rounded-md',
          'bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900',
          'text-[var(--accent)]'
        )}>
          <Sparkles size={14} strokeWidth={2.5} />
        </div>
        
        <span className="group-hover:translate-x-0.5 transition-transform">
          Follow-up questions
        </span>
        
        <ChevronDown 
          size={16} 
          className={clsx(
            'transition-all duration-300 ml-auto',
            'group-hover:text-[var(--text-primary)]',
            expanded && 'rotate-180'
          )}
        />
      </button>
      
      {/* Suggestions Grid */}
      {expanded && (
        <div className="mt-3 space-y-2 pl-0 animate-fade-in">
          {suggestions.map((suggestion, idx) => (
            <button
              key={idx}
              onClick={() => {
                onSuggestionClick(suggestion)
                setExpanded(false)
              }}
              onMouseEnter={() => setHoveredIdx(idx)}
              onMouseLeave={() => setHoveredIdx(null)}
              disabled={disabled}
              className={clsx(
                'group w-full text-left px-3.5 py-2.5 rounded-lg',
                'border transition-all duration-200',
                'flex items-start justify-between gap-3',
                hoveredIdx === idx
                  ? 'bg-[var(--accent)] border-[var(--accent)] text-white shadow-md shadow-[var(--accent)]/20'
                  : 'bg-white dark:bg-[var(--bg-secondary)] border-[var(--border)] text-[var(--text-secondary)]',
                'hover:border-[var(--accent)]',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'cursor-pointer'
              )}
              title={suggestion}
            >
              <span className={clsx(
                'text-sm leading-relaxed flex-1 font-regular',
                'group-hover:text-white transition-colors',
                hoveredIdx === idx ? 'font-medium' : 'font-normal'
              )}>
                {suggestion}
              </span>
              
              <ArrowRight 
                size={16} 
                className={clsx(
                  'flex-shrink-0 mt-0.5 transition-all duration-200',
                  'opacity-0 group-hover:opacity-100',
                  hoveredIdx === idx && 'translate-x-1'
                )}
              />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
