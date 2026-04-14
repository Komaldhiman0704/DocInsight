import React, { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import clsx from 'clsx'

export default function SuggestionsRow({ suggestions, onSuggestionClick, disabled = false }) {
  const [expanded, setExpanded] = useState(false)
  
  if (!suggestions || suggestions.length === 0) return null

  return (
    <div className="w-full mt-3">
      <button
        onClick={() => setExpanded(!expanded)}
        disabled={disabled}
        className={clsx(
          'flex items-center gap-2 text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)]',
          'transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed'
        )}
      >
        <ChevronDown 
          size={14} 
          className={clsx('transition-transform duration-200', expanded && 'rotate-180')}
        />
        <span>Related questions</span>
      </button>
      
      {expanded && (
        <div className="mt-2 space-y-1.5 pl-5">
          {suggestions.map((suggestion, idx) => (
            <button
              key={idx}
              onClick={() => {
                onSuggestionClick(suggestion)
                setExpanded(false)
              }}
              disabled={disabled}
              className={clsx(
                'block w-full text-left text-xs px-2 py-1.5 rounded',
                'text-[var(--text-secondary)] hover:text-[var(--accent)]',
                'hover:bg-[var(--bg-secondary)]',
                'transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed'
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
