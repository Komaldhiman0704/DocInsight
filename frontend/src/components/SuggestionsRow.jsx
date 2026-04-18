import React, { useState } from 'react'
import { ChevronDown, Sparkles } from 'lucide-react'
import clsx from 'clsx'

export default function SuggestionsRow({ suggestions, onSuggestionClick, disabled = false }) {
  const [expanded, setExpanded] = useState(false)
  
  if (!suggestions || suggestions.length === 0) return null

  const handleSuggestionClick = (suggestion) => {
    onSuggestionClick(suggestion)
    setExpanded(false)
  }

  return (
    <div className="w-full mt-6">
      {/* Header Button */}
      <button
        onClick={() => setExpanded(!expanded)}
        disabled={disabled}
        className={clsx(
          'flex items-center gap-2 text-sm font-semibold',
          'text-[var(--text-primary)] hover:text-[var(--accent)]',
          'transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed',
          'p-0'
        )}
      >
        <Sparkles size={16} className="text-[var(--accent)]" />
        
        <span>Related Questions</span>
        
        <ChevronDown 
          size={16} 
          className={clsx(
            'transition-transform duration-300',
            expanded ? 'rotate-180' : ''
          )}
        />
      </button>
      
      {/* Expanded Content */}
      {expanded && (
        <div className={clsx(
          'mt-3 space-y-2 animate-fade-in'
        )}>
          {suggestions.map((suggestion, idx) => (
            <button
              key={idx}
              onClick={() => handleSuggestionClick(suggestion)}
              disabled={disabled}
              className={clsx(
                'w-full text-left px-4 py-3 rounded-lg',
                'border border-[var(--border)]',
                'bg-white dark:bg-[var(--bg-secondary)]',
                'text-[var(--text-secondary)] hover:text-[var(--text-primary)]',
                'hover:border-[var(--accent)] hover:bg-gradient-to-r hover:from-[var(--accent)]/5 hover:to-transparent',
                'transition-all duration-200',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'cursor-pointer text-sm leading-relaxed'
              )}
              title={suggestion}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
