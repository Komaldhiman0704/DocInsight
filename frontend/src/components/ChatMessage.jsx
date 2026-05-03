import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Bot, User } from 'lucide-react'
import SourceCard from './SourceCard'
import SuggestionsRow from './SuggestionsRow'
import ConfidenceIndicator from './ConfidenceIndicator'
import clsx from 'clsx'

// Loading dots animation with thinking text
function ThinkingDots() {
  return (
    <div className="flex items-center gap-2 text-[var(--text-muted)] text-xs">
      <div className="flex gap-1">
        {[0, 1, 2].map(i => (
          <span
            key={i}
            className="w-1.5 h-1.5 rounded-full bg-current animate-pulse-dot"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
      <span className="opacity-60">Thinking...</span>
    </div>
  )
}

export default function ChatMessage({ message, onSuggestionClick, onViewPDF }) {
  const isUser = message.role === 'user'
  const isThinking = message.status === 'thinking'
  const isStreaming = message.status === 'streaming'

  return (
    <div className={clsx('flex gap-3 animate-slide-up', isUser && 'flex-row-reverse')}>
      {/* Avatar */}
      <div className={clsx(
        'shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white mt-0.5',
        isUser ? 'bg-[var(--user-bubble)]' : 'bg-slate-600 dark:bg-slate-700'
      )}>
        {isUser ? <User size={15} /> : <Bot size={15} />}
      </div>

      {/* Bubble */}
      <div className={clsx('max-w-[80%] space-y-1', isUser && 'items-end flex flex-col')}>
        <div className={clsx(
          'rounded-2xl px-4 py-2.5 text-sm leading-relaxed',
          isUser
            ? 'bg-[var(--user-bubble)] text-white rounded-tr-sm'
            : 'bg-[var(--ai-bubble)] border border-[var(--border)] text-[var(--text-primary)] rounded-tl-sm'
        )}>
          {isThinking && <ThinkingDots />}
          {!isThinking && (
            <div className={clsx('prose-message', isStreaming && 'typing-cursor')}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content || ''}
              </ReactMarkdown>
            </div>
          )}

          {/* ✅ PART 5 IMPROVEMENT: Show loading state during streaming */}
          {isStreaming && message.content && (
            <div className="flex items-center gap-2 text-[11px] text-[var(--text-muted)] mt-2 animate-pulse">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-[var(--accent)]"></span>
              Generating answer...
            </div>
          )}
        </div>

        {/* Sources */}
        {!isUser && message.sources?.length > 0 && (
          <div className="w-full">
            <SourceCard sources={message.sources} onViewPDF={onViewPDF} />
          </div>
        )}

        {/* Confidence Indicator */}
        {!isUser && message.status === 'done' && message.confidence && (
          <div className="w-full">
            <ConfidenceIndicator
              confidence={message.confidence}
              relevance_score={message.relevance_score}
              source_count={message.source_count}
              ocr_sources={message.ocr_sources}
            />
          </div>
        )}

        {/* Suggestions */}
        {!isUser && message.status === 'done' && message.suggestions?.length > 0 && onSuggestionClick && (
          <div className="w-full">
            <SuggestionsRow 
              suggestions={message.suggestions}
              onSuggestionClick={onSuggestionClick}
            />
          </div>
        )}

        {/* Timestamp */}
        {message.timestamp && (
          <p className="text-[10px] text-[var(--text-muted)] px-1">
            {new Date(message.timestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
          </p>
        )}
      </div>
    </div>
  )
}
