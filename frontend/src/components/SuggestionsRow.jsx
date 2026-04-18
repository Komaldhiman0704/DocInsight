import React, { useState } from 'react'
import { ChevronDown, Sparkles, ArrowRight, Zap } from 'lucide-react'
import clsx from 'clsx'

export default function SuggestionsRow({ suggestions, onSuggestionClick, disabled = false }) {
  const [expanded, setExpanded] = useState(false)
  const [hoveredIdx, setHoveredIdx] = useState(null)
  const [clickedIdx, setClickedIdx] = useState(null)
  
  if (!suggestions || suggestions.length === 0) return null

  const handleSuggestionClick = (suggestion, idx) => {
    setClickedIdx(idx)
    setTimeout(() => {
      onSuggestionClick(suggestion)
      setExpanded(false)
      setClickedIdx(null)
    }, 150)
  }

  return (
    <div className="w-full mt-6 px-0.5">
      {/* Header Button */}
      <button
        onClick={() => setExpanded(!expanded)}
        disabled={disabled}
        className={clsx(
          'group flex items-center gap-2.5 text-sm font-semibold',
          'text-[var(--text-secondary)] hover:text-[var(--text-primary)]',
          'transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed',
          'rounded-lg px-1 py-1.5'
        )}
      >
        {/* Icon Container */}
        <div className={clsx(
          'flex items-center justify-center w-6 h-6 rounded-lg flex-shrink-0',
          'bg-gradient-to-br from-blue-100 to-blue-200 dark:from-blue-900/50 dark:to-blue-800/50',
          'text-[var(--accent)] transition-all duration-300',
          'group-hover:shadow-lg group-hover:shadow-blue-400/20',
          'group-hover:scale-110'
        )}>
          <Sparkles size={16} strokeWidth={2} />
        </div>
        
        {/* Label */}
        <span className={clsx(
          'transition-all duration-200 font-medium text-[13px]',
          'tracking-tight'
        )}>
          Related Questions
        </span>
        
        {/* Badge */}
        <span className={clsx(
          'ml-auto text-xs font-semibold px-1.5 py-0.5',
          'bg-[var(--accent)]/10 text-[var(--accent)] rounded-md',
          'transition-all duration-200'
        )}>
          {suggestions.length}
        </span>
        
        {/* Chevron */}
        <ChevronDown 
          size={18} 
          className={clsx(
            'transition-all duration-500 flex-shrink-0',
            'text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]',
            expanded ? 'rotate-180 text-[var(--accent)]' : ''
          )}
        />
      </button>
      
      {/* Expanded Content */}
      {expanded && (
        <div className={clsx(
          'mt-3 space-y-2 animate-fade-in overflow-hidden'
        )}>
          {/* Divider */}
          <div className="h-px bg-gradient-to-r from-[var(--border)] via-[var(--border)] to-transparent opacity-50 mb-3" />
          
          {/* Suggestions Grid */}
          <div className={clsx(
            'grid grid-cols-1 md:grid-cols-2 gap-2',
            'transition-all duration-300'
          )}>
            {suggestions.map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => handleSuggestionClick(suggestion, idx)}
                onMouseEnter={() => !disabled && setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
                disabled={disabled}
                className={clsx(
                  'group relative text-left p-3 rounded-lg',
                  'border transition-all duration-200 cursor-pointer',
                  'overflow-hidden',
                  
                  // Base state
                  'bg-gradient-to-br from-white/80 to-white/60',
                  'dark:from-[var(--bg-secondary)]/80 dark:to-[var(--bg-secondary)]/60',
                  'border-[var(--border)] text-[var(--text-secondary)]',
                  
                  // Hover state
                  hoveredIdx === idx && !clickedIdx
                    ? 'border-[var(--accent)]/50 bg-gradient-to-br from-blue-50 to-blue-50/50 dark:from-blue-950/30 dark:to-blue-900/20 shadow-md shadow-[var(--accent)]/10 text-[var(--text-primary)]'
                    : '',
                  
                  // Clicked state
                  clickedIdx === idx
                    ? 'scale-95 opacity-75'
                    : '',
                  
                  // Disabled state
                  'disabled:opacity-50 disabled:cursor-not-allowed',
                  
                  // Flex layout
                  'flex items-center justify-between gap-2.5'
                )}
                title={suggestion}
              >
                {/* Background gradient on hover */}
                <div className={clsx(
                  'absolute inset-0 opacity-0 transition-opacity duration-300',
                  'bg-gradient-to-r from-[var(--accent)]/5 to-transparent',
                  hoveredIdx === idx && 'opacity-100'
                )} />
                
                {/* Zap Icon */}
                <div className={clsx(
                  'flex items-center justify-center w-5 h-5 rounded-md flex-shrink-0',
                  'bg-gradient-to-br from-amber-100 to-orange-100',
                  'dark:from-amber-900/40 dark:to-orange-900/40',
                  'text-amber-600 dark:text-amber-400',
                  'transition-all duration-300',
                  hoveredIdx === idx && 'scale-110 drop-shadow-md'
                )}>
                  <Zap size={14} strokeWidth={2.5} />
                </div>
                
                {/* Text Content */}
                <span className={clsx(
                  'text-sm leading-snug flex-1 font-medium',
                  'transition-all duration-200 truncate',
                  hoveredIdx === idx ? 'text-[var(--text-primary)]' : 'text-[var(--text-secondary)]'
                )}>
                  {suggestion}
                </span>
                
                {/* Arrow Icon */}
                <ArrowRight 
                  size={16} 
                  className={clsx(
                    'flex-shrink-0 transition-all duration-300',
                    'text-[var(--accent)] opacity-0',
                    hoveredIdx === idx && 'opacity-100 translate-x-1'
                  )}
                />
              </button>
            ))}
          </div>
          
          {/* Footer Info */}
          <div className="mt-2 flex items-center gap-1.5 px-1 text-xs text-[var(--text-muted)]">
            <div className="w-1 h-1 rounded-full bg-[var(--text-muted)]" />
            <span>Click any question to explore related topics</span>
          </div>
        </div>
      )}
    </div>
  )
}
